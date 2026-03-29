import mysql.connector

# ✅ Connect to MySQL using correct socket
conn = mysql.connector.connect(
    host="localhost",
    user="yashwant",
    password="1234",                # your MySQL password
    database="yashwant_db",         # your database name
    unix_socket="/var/run/mysqld/mysqld.sock"
)

cursor = conn.cursor()

# Example query
cursor.execute("SELECT * FROM student;")
rows = cursor.fetchall()

for row in rows:
    print(row)

cursor.close()
conn.close()