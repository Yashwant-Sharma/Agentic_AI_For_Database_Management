from agent import agent_loop
from db import get_schema

print("🤖 Agentic AI Database Assistant")
print(f"Current Database Schema:\n{get_schema()}\n")
print("Type 'exit' to quit\n")

while True:
    user_input = input("Enter your query: ").strip()

    if user_input.lower() == "exit":
        print("👋 Goodbye!")
        break

    if not user_input:
        continue

    try:
        response = agent_loop(user_input)
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