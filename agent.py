from langchain_community.llms import Ollama
from db import run_query, get_schema
from utils import requires_confirmation, validate_query
import re

llm = Ollama(model="llama3")


def clean_sql(response: str) -> str:
    if hasattr(response, "content"):
        response = response.content

    text = str(response).strip()

    # remove markdown blocks
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text

    # remove standalone code-fence language label
    text = re.sub(r"(?im)^\s*sql\s*$", "", text).strip()

    # extract only valid SQL lines
    lines = text.splitlines()
    sql_lines = []

    for line in lines:
        line = line.strip()
        if line.lower().startswith((
            "select", "insert", "update",
            "delete", "show", "describe",
            "create", "alter", "drop", "use"
        )):
            sql_lines.append(line)

    cleaned_sql = " ".join(sql_lines).strip()
    if cleaned_sql:
        return cleaned_sql

    # fallback: extract SQL that appears mid-line (e.g., "Here is SQL: SELECT ...")
    pattern = re.compile(
        r"(?is)\b(select|insert|update|delete|show|describe|create|alter|drop|use)\b.*?(?:;|$)"
    )
    matches = [match.group(0).strip() for match in pattern.finditer(text)]
    return " ".join(matches).strip()


def generate_sql(user_query, schema_text):
    prompt = f"""
You are a SQL generator for MySQL.

STRICT RULES:
- Output ONLY SQL query
- DO NOT add explanations
- DO NOT write sentences like "Here is the SQL"
- DO NOT include markdown or text

SPECIAL CASES:
- show databases → SHOW DATABASES;
- show tables → SHOW TABLES;
- in project table show name of those who have age > 30 → SELECT name FROM project WHERE age > 30;

GENERAL RULES:
- Use ONLY tables from schema when querying tables
- If multiple commands → separate with semicolon (;)
- Support DDL and DML: CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, SELECT
- If user asks to create/delete database, return CREATE DATABASE / DROP DATABASE SQL

Schema:
{schema_text}

User Query:
{user_query}
"""

    response = llm.invoke(prompt)
    sql = clean_sql(response)

    # hard fallback to harmless read query
    if not sql.lower().startswith((
        "select", "insert", "update",
        "delete", "show", "describe",
        "create", "alter", "drop", "use"
    )):
        return "SHOW DATABASES;"

    return sql


def explain_action(user_query, sql_query, result):
    # (kept but not used in UI)
    prompt = f"""
You are a database assistant.

RULES:
- Be short and natural
- Do NOT include data
- If error → say "There was an error executing the query"

User Query:
{user_query}

SQL:
{sql_query}

Response:
"""
    response = llm.invoke(prompt)

    if hasattr(response, "content"):
        return response.content.strip()

    return str(response).strip()


def execute_sql(sql_query, db_config, database):
    return run_query(sql_query, db_config=db_config, database=database)


def agent_loop(user_query: str, db_config, database):
    schema_text = get_schema(db_config, database)
    sql_query = generate_sql(user_query, schema_text)

    if not validate_query(sql_query):
        return "❌ Unsafe query detected!", ""

    if requires_confirmation(sql_query):
        return None, sql_query

    result = execute_sql(sql_query, db_config=db_config, database=database)

    return result, sql_query