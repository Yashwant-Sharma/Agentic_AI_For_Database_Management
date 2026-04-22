from urllib.parse import quote_plus

from sqlalchemy import create_engine, text

from utils import split_sql_statements


def _build_engine(db_config, database=None):
    user = db_config.get("user", "")
    password = quote_plus(db_config.get("password", ""))
    host = db_config.get("host", "localhost")
    port = db_config.get("port", 3306)
    unix_socket = db_config.get("unix_socket", "").strip()
    database_name = database if database else ""

    url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database_name}"
    connect_args = {"unix_socket": unix_socket} if unix_socket else {}
    return create_engine(url, connect_args=connect_args)


def test_connection(db_config):
    engine = _build_engine(db_config)
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, "✅ Connected to MySQL"
    except Exception as error:
        return False, f"❌ Connection failed: {error}"
    finally:
        engine.dispose()


def list_databases(db_config):
    engine = _build_engine(db_config)
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SHOW DATABASES"))
            return [row[0] for row in result.fetchall()]
    finally:
        engine.dispose()


def run_query(query, db_config, database=None):
    engine = _build_engine(db_config, database=database)
    try:
        with engine.connect() as conn:
            total_rows = 0
            outputs = []

            for statement in split_sql_statements(query):
                result = conn.execute(text(statement))

                if result.returns_rows:
                    rows = result.fetchall()
                    columns = list(result.keys())
                    outputs.append([columns] + rows)
                else:
                    affected = result.rowcount if result.rowcount and result.rowcount > 0 else 0
                    total_rows += affected
                    outputs.append(f"✅ Query executed ({affected} rows affected)")

            conn.commit()

        if not outputs:
            return "⚠️ No SQL statement executed"
        if len(outputs) == 1:
            return outputs[0]
        return outputs
    except Exception as error:
        return f"❌ Query failed: {error}"
    finally:
        engine.dispose()


def _statement_type(statement: str):
    return statement.strip().split(" ")[0].lower() if statement.strip() else ""


def preview_query(query, db_config, database=None):
    """
    Dry-run preview for risky operations.
    - DML (INSERT/UPDATE/DELETE): execute inside transaction and rollback.
    - DDL (CREATE/ALTER/DROP/TRUNCATE): do not execute; report as non-previewable safely.
    """
    engine = _build_engine(db_config, database=database)
    statements = split_sql_statements(query)

    if not statements:
        return {"ok": True, "summary": "No statements to preview.", "details": []}

    details = []
    try:
        with engine.connect() as conn:
            tx = conn.begin()
            try:
                for statement in statements:
                    kind = _statement_type(statement)
                    if kind in {"create", "alter", "drop", "truncate"}:
                        details.append(
                            {
                                "sql": statement,
                                "type": kind,
                                "preview": "DDL skipped in dry-run to avoid implicit commits in MySQL.",
                            }
                        )
                        continue

                    result = conn.execute(text(statement))
                    if result.returns_rows:
                        rows = result.fetchmany(5)
                        details.append(
                            {
                                "sql": statement,
                                "type": kind,
                                "preview": f"Read-only query previewed ({len(rows)} sample rows captured).",
                            }
                        )
                    else:
                        affected = result.rowcount if result.rowcount and result.rowcount > 0 else 0
                        details.append(
                            {
                                "sql": statement,
                                "type": kind,
                                "preview": f"Would affect approximately {affected} rows (rolled back).",
                            }
                        )
            finally:
                tx.rollback()

        return {"ok": True, "summary": "Dry run completed. No changes were committed.", "details": details}
    except Exception as error:
        return {"ok": False, "summary": f"Dry run failed: {error}", "details": details}
    finally:
        engine.dispose()


def get_schema(db_config, database):
    if not database:
        return "No database selected"

    engine = _build_engine(db_config)
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT table_name, column_name
                    FROM information_schema.columns
                    WHERE table_schema = :db_name
                    ORDER BY table_name, ordinal_position;
                    """
                ),
                {"db_name": database},
            )

            schema = {}
            for table, column in result.fetchall():
                schema.setdefault(table, []).append(column)

            if not schema:
                return f"Database `{database}` has no tables yet."
            return "\n".join([f"{table}: {', '.join(cols)}" for table, cols in schema.items()])
    except Exception as error:
        return f"Error fetching schema: {error}"
    finally:
        engine.dispose()