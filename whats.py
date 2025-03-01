from flask import Flask, request, render_template, jsonify
import requests
import pyodbc
import time
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import random
import subprocess
import os

exe_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "windows-amd64.exe"))

subprocess.Popen(f'start "" "{exe_path}"', shell=True)


app = Flask(__name__)

# Database credentials
DB_CONFIG = {
    "server": "192.168.112.12",
    "database": "crmtest",
    "username": "root",
    "password": "polka@1122",
    "driver": "{ODBC Driver 17 for SQL Server}",
}

# API base URL
BASE_URL = "http://localhost:3000/send"

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
)

# Create a session with retry logic
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)

def get_db_connection():
    """Establishes a new database connection."""
    return pyodbc.connect(
        f"DRIVER={DB_CONFIG['driver']};SERVER={DB_CONFIG['server']};"
        f"DATABASE={DB_CONFIG['database']};UID={DB_CONFIG['username']};PWD={DB_CONFIG['password']}"
    )

def get_phone_numbers(lead_officer, start_date=None, end_date=None):
    """Fetch phone numbers from the database with optional date filtering."""
    query = """
        SELECT DISTINCT CONCAT(d.country_code, a.memberId) AS Phone_number
        FROM CRM_member_info_leads AS a
        LEFT JOIN CRM_member_info_hds AS d ON a.memberId = d.client_id
        WHERE a.lead_officer = ?
    """
    params = [lead_officer]

    if start_date and end_date:
        query += " AND a.posting_date BETWEEN ? AND ?"
        params.extend([start_date, end_date])

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    phone_numbers = [row[0] for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return phone_numbers

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        message = request.form.get("message", "").strip()
        lead_officer = request.form.get("lead_officer", "").strip()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        files = request.files.getlist("file")

        if not lead_officer:
            return jsonify({"error": "Lead Officer is required"}), 400

        phone_numbers = get_phone_numbers(lead_officer, start_date, end_date)
        responses = []

        batch_size = 10
        for i in range(0, len(phone_numbers), batch_size):
            batch = phone_numbers[i:i+batch_size]

            for phone_number in batch:
                if phone_number.startswith("+92") and len(phone_number) == 13:
                    phone_with_suffix = f"{phone_number}@s.whatsapp.net"
                    logger.debug(f"Sending to: {phone_with_suffix}")
                    delay = random.randint(5, 10)
                    time.sleep(delay)

                    if message:
                        text_payload = {
                            "phone": phone_with_suffix,
                            "message": message,
                            "reply_message_id": request.form.get("reply_message_id", ""),
                        }
                        try:
                            response = session.post(f"{BASE_URL}/message", json=text_payload, timeout=10)
                            response.raise_for_status()
                            responses.append(response.json())
                        except requests.exceptions.RequestException as e:
                            logger.error(f"Failed to send text message: {e}")
                            responses.append({"error": str(e)})

                    for file in files:
                        if file:
                            file_extension = file.filename.split('.')[-1].lower()
                            media_type = None

                            if file_extension in ["jpg", "jpeg", "png", "gif"]:
                                media_type = "image"
                            elif file_extension in ["mp3", "wav", "aac"]:
                                media_type = "audio"
                            elif file_extension in ["mp4", "mkv", "avi"]:
                                media_type = "video"

                            if media_type:
                                file.stream.seek(0)
                                media_payload = {
                                    "phone": (None, phone_with_suffix),
                                    "view_once": (None, "false"),
                                    "compress": (None, "false"),
                                    media_type: (file.filename, file.stream, file.mimetype),
                                }
                                media_url = f"{BASE_URL}/{media_type}"

                                try:
                                    response = session.post(media_url, files=media_payload, timeout=10)
                                    response.raise_for_status()
                                    responses.append(response.json())
                                except requests.exceptions.RequestException as e:
                                    logger.error(f"Failed to send file: {e}")
                                    responses.append({"error": str(e)})
                            else:
                                responses.append({"error": f"Unsupported file type: {file.filename}"})

            if i + batch_size < len(phone_numbers):
                logger.debug("Batch processed, waiting 15 seconds before next batch...")
                time.sleep(15)

        if not message and not files:
            return jsonify({"error": "No content to send"}), 400

        return jsonify(responses)

    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)  



