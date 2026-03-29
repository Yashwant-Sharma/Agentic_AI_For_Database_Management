from langchain_community.llms import Ollama
from db import run_query, get_schema
from utils import validate_query

llm = Ollama(model="llama3")

def clean_sql(response: str) -> str:
    if "```" in response:
        response = response.split("```")[1]
    return response.strip()

def generate_sql(user_query: str) -> str:
    prompt = f"""
You are a SQL generator.

RULES:
- You may generate SELECT, INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE queries
- Use ONLY the tables present in the schema below
- Output ONLY raw SQL (no explanation, no markdown)
- Ensure column count matches table schema

Schema:
{get_schema()}

User Query:
{user_query}
"""
    response = llm.invoke(prompt)
    return clean_sql(response)

def agent_loop(user_query: str):
    print("\n🧠 Thinking...")
    sql_query = generate_sql(user_query)
    print("Generated SQL:", sql_query)

    if not validate_query(sql_query):
        return "❌ Unsafe query detected!"

    result = run_query(sql_query)
    return result