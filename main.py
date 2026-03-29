# main.py
from agent import agent_loop
from db import get_schema

print(get_schema())

print("🤖 Agentic AI Database Assistant")
print("Type 'exit' to quit\n")

while True:
    user_input = input("Enter your query: ")

    if user_input.lower() == "exit":
        break

    try:
        response = agent_loop(user_input)
    except Exception as e:
        response = f"Error during query execution: {e}"

    print("📊 Result:", response)