# agent.py
from langchain_community.llms import Ollama
from db import run_query, get_schema
from utils import validate_query

llm = Ollama(model="llama3")

def clean_sql(response):
    if "```" in response:
        response = response.split("```")[1]
    return response.strip()

def generate_sql(user_query):
    prompt = f"""
    You are a SQL generator.

    STRICT RULES:
    - ONLY generate SELECT queries
    - DO NOT use INSERT, UPDATE, DELETE, DROP, ALTER, GRANT, REVOKE
    - Use ONLY the tables present in the schema below
    - Output ONLY raw SQL (no explanation, no markdown)

    Schema:
    {get_schema()}

    User Query:
    {user_query}
    """
    response = llm.invoke(prompt)
    return clean_sql(response)

def agent_loop(user_query):
    print("\n🧠 Thinking...")
    sql_query = generate_sql(user_query)
    print("Generated SQL:", sql_query)

    if not validate_query(sql_query):
        return "❌ Unsafe query detected!"

    result = run_query(sql_query)

    if isinstance(result, str) and result.startswith("Query error"):
        print("⚠️ Error detected. Fixing...")
        fix_prompt = f"""
        Fix this SQL query.

        STRICT RULES:
        - ONLY SELECT queries
        - No permission or admin commands
        - Use only given schema

        Query:
        {sql_query}

        Error:
        {result}

        Return ONLY SQL.
        """
        fixed_query = clean_sql(llm.invoke(fix_prompt))
        print("Fixed SQL:", fixed_query)

        if not validate_query(fixed_query):
            return "❌ Unsafe fixed query blocked!"

        result = run_query(fixed_query)

    return result