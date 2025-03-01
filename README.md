# whatsapp-blast-with-sqldatabase
This project allows you to fetch phone numbers one by one from an SQL Server database and send messages to clients automatically. To use this, install Python, set up your database, configure the ODBC driver, and provide your database credentials along with the required query. Then, run the provided code to start sending messages.


# Prerequisites  

Ensure you have the following installed before proceeding:  

- **Python 3.x**  
- **SQL Server with ODBC Driver**  
- **FFmpeg** (for media processing)  
- **Go-WhatsApp Web MultiDevice** dependencies  

## Installation Steps  

### 1. Install Required Dependencies  
Run the following command to install Python dependencies:  
note
if you have any erorr you can visit 
https://github.com/aldinokemal/go-whatsapp-web-multidevice?tab=readme-ov-file
read instalation instrunction

```bash
 install docker desktop and run in cmd

 docker run --detach --publish=3000:3000 --name=whatsapp --restart=always --volume=$(docker volume create --name=whatsapp):/app/storages aldinokemal2104/go-whatsapp-web-multidevice --autoreply="Dont't reply this message please"
pip install -r requirements.txt


