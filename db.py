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
            change_made = False

            queries = [q.strip() for q in query.split(";") if q.strip()]

            for q in queries:
                result = conn.execute(text(q))

                # ✅ If query returns rows (SELECT, SHOW, DESCRIBE)
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = list(result.keys())
                    final_result = [columns] + rows

                else:
                    # ✅ Only count real changes
                    if result.rowcount and result.rowcount > 0:
                        total_rows += result.rowcount
                        change_made = True

            conn.commit()

        # ✅ Return data if exists
        if final_result:
            return final_result

        # ✅ Only show success if change happened
        if change_made:
            return f"✅ Changes applied ({total_rows} rows affected)"

        # ✅ No change case
        return "⚠️ No changes were made"

    except Exception as e:
        return f"❌ Query failed: {e}"

def get_schema():
    ensure_database_and_tables()
    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                f"""
                SELECT table_name, column_name
                FROM information_schema.columns
                WHERE table_schema = '{DB_NAME}'
                ORDER BY table_name;
                """
            ))

            schema = {}
            for table, column in result.fetchall():
                schema.setdefault(table, []).append(column)

            return "\n".join([f"{t}: {', '.join(c)}" for t, c in schema.items()])

    except Exception as e:
        return f"Error fetching schema: {e}"