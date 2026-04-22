import streamlit as st
import pandas as pd
import re
from agent import agent_loop
from db import list_databases, preview_query, run_query, test_connection

st.set_page_config(page_title="Agentic AI DB Assistant", layout="wide")
st.title("🧠 Agentic AI Database Assistant")

if "history" not in st.session_state:
    st.session_state.history = []
if "connected" not in st.session_state:
    st.session_state.connected = False
if "db_config" not in st.session_state:
    st.session_state.db_config = {}
if "selected_database" not in st.session_state:
    st.session_state.selected_database = ""
if "databases" not in st.session_state:
    st.session_state.databases = []
if "pending_action" not in st.session_state:
    st.session_state.pending_action = None
if "pending_actions" not in st.session_state:
    st.session_state.pending_actions = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None
if "change_log" not in st.session_state:
    st.session_state.change_log = []
if "dry_run_mode" not in st.session_state:
    st.session_state.dry_run_mode = False


def render_result(result):
    if isinstance(result, dict) and result.get("mode") == "dry-run":
        st.info(f"🧪 {result.get('summary', 'Dry run completed.')}")
        for detail in result.get("details", []):
            st.markdown(f"- `{detail.get('sql', '')}`")
            st.caption(detail.get("preview", "No preview details available."))
        return

    if isinstance(result, list):
        if not result:
            st.info("📭 No data found")
            return

        if len(result) > 0 and isinstance(result[0], list) and result[0] and isinstance(result[0][0], str):
            columns = result[0]
            rows = result[1:]
            if not rows:
                st.info("📭 No data found")
                return
            df = pd.DataFrame(rows, columns=columns)
            st.dataframe(df, use_container_width=True)
            return

        for idx, each in enumerate(result, start=1):
            st.markdown(f"**Result {idx}**")
            render_result(each)
        return

    result_str = str(result)
    if "❌" in result_str or "error" in result_str.lower():
        st.error(result_str)
    elif "✅" in result_str:
        st.success(result_str)
    elif "⚠️" in result_str:
        st.warning(result_str)
    else:
        st.info(result_str)


def add_assistant_message(message: str):
    st.session_state.chat_history.append({"role": "assistant", "content": message})


def classify_sql_action(sql: str):
    first_word = sql.strip().split(" ")[0].lower() if sql.strip() else ""
    if first_word in {"insert", "update", "delete", "create", "alter", "drop", "truncate"}:
        return first_word
    return "other"


def summarize_recent_changes(action_type=None):
    if not st.session_state.change_log:
        return "I have not made any database changes yet in this session."

    filtered = st.session_state.change_log
    if action_type:
        filtered = [item for item in filtered if item["action"] == action_type]
        if not filtered:
            return f"I have not executed any `{action_type.upper()}` operation yet in this session."

    recent = filtered[-5:]
    lines = []
    for item in reversed(recent):
        lines.append(f"- `{item['sql']}` -> {item['result']}")
    return "Here are the most recent changes I made:\n" + "\n".join(lines)


def extract_database_name(text: str, action: str):
    if action == "create":
        pattern = r"create\s+database\s+(?:named\s+)?`?([a-zA-Z0-9_]+)`?"
    else:
        pattern = r"(?:delete|drop)\s+database\s+(?:named\s+)?`?([a-zA-Z0-9_]+)`?"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def split_commands(query_text: str):
    return [part.strip() for part in query_text.split(",") if part.strip()]


def extract_table_name(text: str):
    match = re.search(r"create\s+table\s+(?:if\s+not\s+exists\s+)?`?([a-zA-Z0-9_]+)`?", text, flags=re.IGNORECASE)
    return match.group(1) if match else None


def contains_column_definition(text: str):
    normalized = text.lower()
    return "(" in text and ")" in text or "column" in normalized or "columns" in normalized


def try_parse_insert_assignment(command_text: str):
    """
    Parse patterns like:
    - insert name=tarun age=18 score=49 into project table
    - insert name=tarun,age=18,score=49 into project
    """
    lower = command_text.lower()
    if not lower.startswith("insert") or "=" not in command_text or "into" not in lower:
        return None

    table_match = re.search(r"\binto\s+`?([a-zA-Z0-9_]+)`?(?:\s+table)?\b", command_text, flags=re.IGNORECASE)
    if not table_match:
        return None
    table_name = table_match.group(1)

    assignments_part = command_text[: table_match.start()]
    assignments = re.findall(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*([^,\s]+)", assignments_part)
    if not assignments:
        return None

    columns = []
    values = []
    for column, raw_value in assignments:
        value = raw_value.strip().strip("'").strip('"')
        columns.append(column)
        if re.fullmatch(r"-?\d+(\.\d+)?", value):
            values.append(value)
        else:
            safe_value = value.replace("'", "''")
            values.append(f"'{safe_value}'")

    columns_sql = ", ".join(columns)
    values_sql = ", ".join(values)
    return f"INSERT INTO {table_name} ({columns_sql}) VALUES ({values_sql});"


def queue_table_create_action(table_name: str, columns_sql: str, command_text: str):
    sql = f"CREATE TABLE {table_name} ({columns_sql});"
    queue_or_preview_action(command_text, sql)
    add_assistant_message(f"I prepared table creation for `{table_name}`.")


def is_auto_schema_reply(text: str):
    normalized = text.strip().lower()
    return normalized in {
        "make by yourself",
        "make it by yourself",
        "you decide",
        "decide yourself",
        "auto",
        "automatic",
    }


def default_columns_for_table():
    return "id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"


def generate_preview(sql: str):
    db_name = st.session_state.selected_database
    if sql.lower().startswith(("create database", "drop database")):
        db_name = None
    return preview_query(sql, db_config=st.session_state.db_config, database=db_name)


def queue_or_preview_action(command_text: str, sql: str):
    preview = generate_preview(sql)
    if st.session_state.dry_run_mode:
        dry_result = {
            "mode": "dry-run",
            "summary": preview["summary"],
            "details": preview.get("details", []),
        }
        st.session_state.history.append({"query": command_text, "sql": sql, "result": dry_result})
        add_assistant_message("Dry run completed. No changes were committed.")
        return

    st.session_state.pending_actions.append({"query": command_text, "sql": sql, "preview": preview})
    add_assistant_message("I prepared a write operation with impact preview. Please confirm below before execution.")


def queue_db_action(command_text: str, db_name: str, action: str):
    if action == "create":
        sql = f"CREATE DATABASE {db_name};"
        summary = f"You asked to create database `{db_name}`."
    else:
        sql = f"DROP DATABASE {db_name};"
        summary = f"You asked to delete database `{db_name}`."

    queue_or_preview_action(command_text, sql)
    add_assistant_message(summary)


def process_command(command_text: str):
    lower_text = command_text.lower()

    if lower_text in {"hi", "hello", "hey"}:
        add_assistant_message(
            "Hello! I can help with database and table operations. Try: `show tables` or `create database mydb`."
        )
        return

    if "help" in lower_text:
        add_assistant_message(
            "Try commands like: `show databases`, `show tables`, `create database mydb`, `delete database mydb`, or data queries."
        )
        return

    if "what you deleted" in lower_text or "what did you delete" in lower_text:
        add_assistant_message(summarize_recent_changes("delete"))
        return

    if "what changes" in lower_text or "what did you change" in lower_text:
        add_assistant_message(summarize_recent_changes())
        return

    if "create database" in lower_text:
        db_name = extract_database_name(command_text, "create")
        if db_name:
            queue_db_action(command_text, db_name, "create")
        else:
            st.session_state.pending_prompt = "create_database_name"
            add_assistant_message("What would you like to name your database?")
        return

    if "delete database" in lower_text or "drop database" in lower_text:
        db_name = extract_database_name(command_text, "drop")
        if db_name:
            queue_db_action(command_text, db_name, "drop")
        else:
            st.session_state.pending_prompt = "delete_database_name"
            add_assistant_message("Which database do you want to delete?")
        return

    if "create table" in lower_text:
        table_name = extract_table_name(command_text)
        if not table_name:
            st.session_state.pending_prompt = {"type": "create_table_name"}
            add_assistant_message("What should be the table name?")
            return

        if not contains_column_definition(command_text):
            st.session_state.pending_prompt = {"type": "create_table_columns", "table_name": table_name}
            add_assistant_message(
                f"What columns should `{table_name}` have? You can also say `make by yourself`."
            )
            return

    parsed_insert_sql = try_parse_insert_assignment(command_text)
    if parsed_insert_sql:
        queue_or_preview_action(command_text, parsed_insert_sql)
        add_assistant_message("I parsed your insert command and prepared it for preview/confirmation.")
        return

    result, sql_query = agent_loop(
        command_text,
        db_config=st.session_state.db_config,
        database=st.session_state.selected_database,
    )

    if result is None:
        queue_or_preview_action(command_text, sql_query)
    else:
        st.session_state.history.append({"query": command_text, "sql": sql_query, "result": result})
        add_assistant_message("Done. I executed your request and added the result in Query History.")


with st.sidebar:
    st.header("🔐 DB Connection")
    user = st.text_input("Username", value=st.session_state.db_config.get("user", ""))
    password = st.text_input("Password", value=st.session_state.db_config.get("password", ""), type="password")

    db_config = {
        "host": "localhost",
        "port": 3306,
        "user": user.strip(),
        "password": password,
        "unix_socket": "/var/run/mysqld/mysqld.sock",
    }

    if st.button("Connect to MySQL"):
        ok, message = test_connection(db_config)
        if ok:
            st.session_state.connected = True
            st.session_state.db_config = db_config
            st.session_state.databases = list_databases(db_config)
            st.success(message)
        else:
            st.session_state.connected = False
            st.error(message)

    st.divider()
    st.session_state.dry_run_mode = st.checkbox(
        "Dry run mode (preview only, no commit)",
        value=st.session_state.dry_run_mode,
    )

if st.session_state.connected:
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.databases:
            current_index = 0
            if st.session_state.selected_database in st.session_state.databases:
                current_index = st.session_state.databases.index(st.session_state.selected_database)
            selected_database = st.selectbox("Active database", st.session_state.databases, index=current_index)
            st.session_state.selected_database = selected_database
        else:
            st.warning("No databases found. Create one to continue.")
            st.session_state.selected_database = ""

    with col2:
        if st.button("Refresh DB List"):
            st.session_state.databases = list_databases(st.session_state.db_config)
            st.rerun()

    st.subheader("💬 Natural Language Query")
    user_query = st.text_input("Enter your query in natural language (you can add multiple commands separated by commas):")

    if st.button("Generate and Execute") and user_query.strip():
        try:
            clean_text = user_query.strip()
            st.session_state.chat_history.append({"role": "user", "content": clean_text})

            if st.session_state.pending_prompt:
                prompt_state = st.session_state.pending_prompt
                clear_prompt = True
                if prompt_state == "create_database_name":
                    db_name = clean_text.split(",")[0].replace("`", "").replace(";", "").strip()
                    queue_db_action(f"create database {db_name}", db_name, "create")
                elif prompt_state == "delete_database_name":
                    db_name = clean_text.split(",")[0].replace("`", "").replace(";", "").strip()
                    queue_db_action(f"delete database {db_name}", db_name, "drop")
                elif isinstance(prompt_state, dict) and prompt_state.get("type") == "create_table_name":
                    table_name = clean_text.split(",")[0].replace("`", "").replace(";", "").strip()
                    st.session_state.pending_prompt = {"type": "create_table_columns", "table_name": table_name}
                    add_assistant_message(
                        f"Great. What columns should `{table_name}` have? You can also say `make by yourself`."
                    )
                    clear_prompt = False
                elif isinstance(prompt_state, dict) and prompt_state.get("type") == "create_table_columns":
                    table_name = prompt_state.get("table_name")
                    if is_auto_schema_reply(clean_text):
                        columns_sql = default_columns_for_table()
                    else:
                        columns_sql = clean_text.replace(";", "").strip()
                    queue_table_create_action(
                        table_name=table_name,
                        columns_sql=columns_sql,
                        command_text=f"create table {table_name}",
                    )
                if clear_prompt:
                    st.session_state.pending_prompt = None
            else:
                commands = split_commands(clean_text)
                for command in commands:
                    process_command(command)

                if len(commands) > 1:
                    add_assistant_message("I processed multiple commands from your single input.")

        except Exception as error:
            st.session_state.history.append({"query": user_query, "sql": "", "result": f"⚠️ Error: {error}"})
            add_assistant_message(f"I hit an error: {error}")

if st.session_state.pending_actions:
    st.subheader("⚠️ Confirmation Required")
    st.warning("These actions can modify data/schema. Preview is generated using rollback-safe dry run.")
    for pending in st.session_state.pending_actions:
        st.markdown(f"**Request:** {pending['query']}")
        st.code(pending["sql"], language="sql")
        preview = pending.get("preview")
        if preview:
            if preview.get("ok"):
                st.caption(preview.get("summary", "Dry run completed."))
            else:
                st.error(preview.get("summary", "Dry run failed."))
            for detail in preview.get("details", []):
                st.caption(f"- {detail.get('preview', '')}")

    confirm_col, cancel_col = st.columns(2)
    with confirm_col:
        if st.button("✅ Confirm and Run"):
            for pending in st.session_state.pending_actions:
                sql = pending["sql"]
                db_name = st.session_state.selected_database
                if sql.lower().startswith(("create database", "drop database")):
                    db_name = None
                result = run_query(sql, db_config=st.session_state.db_config, database=db_name)
                st.session_state.history.append({"query": pending["query"], "sql": sql, "result": result})
                st.session_state.change_log.append(
                    {
                        "action": classify_sql_action(sql),
                        "sql": sql,
                        "result": str(result),
                    }
                )
            st.session_state.pending_actions = []
            st.session_state.databases = list_databases(st.session_state.db_config)
            add_assistant_message("Confirmed. I executed the pending actions.")
            st.rerun()

    with cancel_col:
        if st.button("❌ Cancel"):
            st.session_state.pending_actions = []
            add_assistant_message("Action cancelled. No changes were made.")
            st.info("Action cancelled.")

history_col, clear_col = st.columns([3, 1])
with history_col:
    st.subheader("📊 Query History")
with clear_col:
    if st.button("🧹 Clear History"):
        st.session_state.chat_history = []
        st.session_state.history = []
        st.session_state.pending_actions = []
        st.session_state.pending_prompt = None
        st.session_state.change_log = []
        st.rerun()
for entry in reversed(st.session_state.history):
    with st.expander(f"💬 {entry['query']}", expanded=False):
        if entry.get("sql"):
            st.code(entry["sql"], language="sql")
        render_result(entry["result"])

if not st.session_state.connected:
    st.info("Use the sidebar to connect with your DB username/password.")