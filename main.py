from agent import agent_loop
from db import get_schema, run_query, test_connection


print("🤖 Agentic AI Database Assistant")

db_config = {
    "host": input("Host (default localhost): ").strip() or "localhost",
    "port": int((input("Port (default 3306): ").strip() or "3306")),
    "user": input("DB Username: ").strip(),
    "password": input("DB Password: ").strip(),
    "unix_socket": input("Unix socket (optional): ").strip(),
}
database = input("Database to use (optional): ").strip() or None

ok, message = test_connection(db_config)
print(message)
if not ok:
    raise SystemExit(1)

if database:
    print(f"Current Database Schema:\n{get_schema(db_config, database)}\n")

print("Type 'exit' to quit\n")

while True:
    user_input = input("Enter your query: ").strip()

    if user_input.lower() == "exit":
        print("👋 Goodbye!")
        break

    if not user_input:
        continue

    try:
        response, sql = agent_loop(user_input, db_config=db_config, database=database)
        if response is None:
            print(f"Generated SQL:\n{sql}")
            confirm = input("This will modify data/schema. Confirm? (yes/no): ").strip().lower()
            if confirm == "yes":
                response = run_query(sql, db_config=db_config, database=database)
            else:
                response = "⚠️ Action cancelled"
    except Exception as e:
        response = f"Error during query execution: {e}"

    if isinstance(response, list):
        if len(response) == 0:
            print("📊 Result: Table is empty or no rows matched")
        else:
            print("📊 Result (rows):")
            for row in response:
                print(row)
    else:
        print("📊 Result:", response)