# db.py
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# ✅ Connect to the correct database
DB_NAME = "yashwant_db"

engine = create_engine(
    f"mysql+pymysql://yashwant:1234@localhost/{DB_NAME}",
    connect_args={"unix_socket": "/var/run/mysqld/mysqld.sock"}
)

def ensure_database_and_table():
    # Create database if missing
    temp_engine = create_engine(
        "mysql+pymysql://yashwant:1234@localhost",
        connect_args={"unix_socket": "/var/run/mysqld/mysqld.sock"}
    )
    with temp_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
    temp_engine.dispose()

    # Create table if missing
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS student (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50),
                age INT,
                course VARCHAR(50)
            )
        """))

def run_query(query):
    try:
        ensure_database_and_table()
        with engine.connect() as conn:
            result = conn.execute(text(query))
            if result.returns_rows:
                return result.fetchall()
            return "Query executed successfully"
    except OperationalError as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"Query error: {e}"

def get_schema():
    ensure_database_and_table()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                f"SELECT table_name FROM information_schema.tables WHERE table_schema='{DB_NAME}';"
            ))
            tables = [row[0] for row in result.fetchall()]
            return f"Tables in {DB_NAME}: {tables}"
    except Exception as e:
        return f"Error fetching schema: {e}"