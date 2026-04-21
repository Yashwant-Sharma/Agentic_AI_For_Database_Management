from langchain_community.llms import Ollama
from db import run_query, get_schema
from utils import validate_query

llm = Ollama(model="llama3")


def clean_sql(response: str) -> str:
    if hasattr(response, "content"):
        response = response.content

    text = str(response).strip()

    # remove markdown blocks
    if "```" in text:
        parts = text.split("```")
        text = parts[1] if len(parts) > 1 else text

    # remove common unwanted words
    text = text.replace("sql", "").strip()

    # extract only valid SQL lines
    lines = text.splitlines()
    sql_lines = []

    for line in lines:
        line = line.strip()
        if line.lower().startswith((
            "select", "insert", "update",
            "delete", "show", "describe"
        )):
            sql_lines.append(line)

    cleaned_sql = " ".join(sql_lines)

    return cleaned_sql.strip()


def generate_sql(user_query):
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
- describe student → DESCRIBE student;
- show data of project → SELECT * FROM project;
- show data of student → SELECT * FROM student;

GENERAL RULES:
- Use ONLY tables from schema
- If multiple commands → separate with semicolon (;)

Schema:
{get_schema()}

User Query:
{user_query}
"""

    response = llm.invoke(prompt)
    sql = clean_sql(response)

    # 🚨 hard safety fallback
    if not sql.lower().startswith((
        "select", "insert", "update",
        "delete", "show", "describe"
    )):
        return "SELECT * FROM project;"

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


def execute_multiple(sql_query):
    queries = [q.strip() for q in sql_query.split(";") if q.strip()]
    results = []

    for q in queries:
        res = run_query(q)
        results.append(res)

    return results if len(results) > 1 else results[0]


def agent_loop(user_query: str):
    sql_query = generate_sql(user_query)

    if not validate_query(sql_query):
        return "❌ Unsafe query detected!", ""

    result = execute_multiple(sql_query)

    # explanation removed from UI flow
    return result, ""