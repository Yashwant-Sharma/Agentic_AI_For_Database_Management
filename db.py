from sqlalchemy import create_engine, text

DB_NAME = "yashwant_db"

engine = create_engine(
    f"mysql+pymysql://yashwant:1234@localhost/{DB_NAME}",
    connect_args={"unix_socket": "/var/run/mysqld/mysqld.sock"}
)

def ensure_database_and_tables():
    temp_engine = create_engine(
        "mysql+pymysql://yashwant:1234@localhost",
        connect_args={"unix_socket": "/var/run/mysqld/mysqld.sock"}
    )
    with temp_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
    temp_engine.dispose()

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS student (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(50),
                age INT,
                course VARCHAR(50)
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS project (
                name VARCHAR(255),
                age INT,
                score FLOAT
            )
        """))

def run_query(query):
    ensure_database_and_tables()
    try:
        with engine.begin() as conn:
            result = conn.execute(text(query))
            if result.returns_rows:
                return result.fetchall()
            return "Query executed successfully"
    except Exception as e:
        return f"Database error: {e}"

def get_schema():
    ensure_database_and_tables()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                f"SELECT table_name FROM information_schema.tables WHERE table_schema='{DB_NAME}';"
            ))
            tables = [row[0] for row in result.fetchall()]
            return f"Tables in {DB_NAME}: {tables}"
    except Exception as e:
        return f"Error fetching schema: {e}"