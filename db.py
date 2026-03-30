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
    try:
        with engine.connect() as conn:
            total_rows = 0
            final_result = None

            for q in query.split(";"):
                if q.strip():
                    result = conn.execute(text(q))

                    # ✅ If SELECT query → fetch data with column names
                    if q.strip().lower().startswith("select"):
                        rows = result.fetchall()
                        columns = result.keys()
                        final_result = [columns] + rows
                    else:
                        total_rows += result.rowcount

            conn.commit()

        if final_result:
            return final_result
        return f"✅ Done ({total_rows} rows affected)"

    except Exception as e:
        return f"❌ Query failed: {e}"

    except Exception as e:
        return f"❌ Query failed: {e}"

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