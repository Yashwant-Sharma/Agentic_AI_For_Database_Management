# app.py
import streamlit as st
import pandas as pd
from agent import agent_loop
from db import run_query

st.set_page_config(page_title="Agentic AI DB Assistant", layout="wide")
st.title("🧠 Agentic AI Database Assistant")

if "history" not in st.session_state:
    st.session_state.history = []

# User input
user_query = st.text_input("Enter your query in natural language:")

if st.button("Execute") and user_query.strip() != "":
    try:
        # Run AI agent
        result = agent_loop(user_query)
        # Store in history
        st.session_state.history.append({
            "query": user_query,
            "result": result
        })
    except Exception as e:
        st.session_state.history.append({
            "query": user_query,
            "result": f"⚠️ Error: {e}"
        })

st.subheader("Query History")

# Display each query nicely
for entry in reversed(st.session_state.history):
    with st.expander(f"💬 Query: {entry['query']}", expanded=True):
        # If result is a list of tuples (rows), show as DataFrame
        if isinstance(entry["result"], list):
            try:
                df = pd.DataFrame(entry["result"])
                if df.empty:
                    st.info("✅ Query executed successfully (No rows returned)")
                else:
                    st.dataframe(df)
            except Exception:
                st.write(entry["result"])
        # If result is a string (error or success)
        else:
            if "error" in str(entry["result"]).lower():
                st.error(entry["result"])
            else:
                st.success(entry["result"])