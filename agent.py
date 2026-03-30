from langchain_community.llms import Ollama
from db import run_query, get_schema
from utils import validate_query

llm = Ollama(model="llama3")


# ✅ FIXED: Clean SQL properly (supports multi-query)
def clean_sql(response: str) -> str:
    if hasattr(response, "content"):
        response = response.content

    sql = response.strip()

    # remove markdown formatting
    if "```" in sql:
        parts = sql.split("```")
        sql = parts[1] if len(parts) > 1 else sql

    sql = sql.replace("sql", "").strip()

    return sql


# ✅ FIXED: Strong prompt
def generate_sql(user_query):
    prompt = f"""
You are a SQL generator.

RULES:
- Use ONLY the tables present in the schema
- Output ONLY raw SQL (NO explanation, NO text)
- NEVER combine unrelated updates into one query
- If user asks for multiple DIFFERENT operations, generate MULTIPLE SQL queries separated by semicolon (;)
- Each query must be valid MySQL syntax
- Do not add comments or explanations

Schema:
{get_schema()}

User Query:
{user_query}
"""

    response = llm.invoke(prompt)

    # 🔍 Debug (VERY IMPORTANT)
    print("\n🔍 Raw LLM Output:\n", response)

    return clean_sql(response)


# ✅ FINAL AGENT LOOP
def agent_loop(user_query: str):
    print("\n🧠 Thinking...")

    sql_query = generate_sql(user_query)

    print("\n✅ Cleaned SQL:\n", sql_query)

    # Safety check
    if not validate_query(sql_query):
        return "❌ Unsafe query detected!"

    # Execute
    result = run_query(sql_query)

    return result