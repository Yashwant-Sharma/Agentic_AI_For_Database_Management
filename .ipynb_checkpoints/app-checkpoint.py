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

st.subheader("📊 Query History")

for entry in reversed(st.session_state.history):
    with st.expander(f"💬 {entry['query']}", expanded=True):

        result = entry["result"]

        # ✅ TABLE OUTPUT (SELECT queries)
        if isinstance(result, list):
            if len(result) == 0:
                st.info("📭 No data found")
            else:
        # ✅ First row = column names, rest = data
               columns = result[0]
               rows = result[1:]

               df = pd.DataFrame(rows, columns=columns)

               st.dataframe(df, use_container_width=True)

        # ✅ STRING OUTPUT (INSERT/UPDATE/ERROR)
        else:
            result_str = str(result)

            if "❌" in result_str or "error" in result_str.lower():
                st.error(result_str)

            elif "✅" in result_str:
                st.success(result_str)

            else:
                st.info(result_str)