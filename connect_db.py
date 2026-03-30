import mysql.connector
from dotenv import load_dotenv
import os

# Load environment variables from .env
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME"),
    unix_socket=os.getenv("DB_SOCKET")
)

cursor = conn.cursor()

# Example query
cursor.execute("SELECT * FROM student;")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()