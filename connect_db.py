import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="yashwant",
    password="1234",
    database="yashwant_db",
    unix_socket="/var/run/mysqld/mysqld.sock"
)

cursor = conn.cursor()

cursor.execute("SELECT * FROM student;")
rows = cursor.fetchall()

print("Data in student table:")
for row in rows:
    print(row)

cursor.close()
conn.close()