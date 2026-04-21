import streamlit as st
import pandas as pd
from agent import agent_loop

st.set_page_config(page_title="Agentic AI DB Assistant", layout="wide")
st.title("🧠 Agentic AI Database Assistant")

if "history" not in st.session_state:
    st.session_state.history = []

user_query = st.text_input("Enter your query in natural language:")

if st.button("Execute") and user_query.strip() != "":
    commands = [cmd.strip() for cmd in user_query.split(",") if cmd.strip()]

    for command in commands:
        try:
            result, _ = agent_loop(command)  # ignore explanation

            st.session_state.history.append({
                "query": command,
                "result": result
            })

        except Exception as e:
            st.session_state.history.append({
                "query": command,
                "result": f"⚠️ Error: {e}"
            })

st.subheader("📊 Query History")

for entry in reversed(st.session_state.history):
    with st.expander(f"💬 {entry['query']}", expanded=True):

        result = entry["result"]

        # ✅ TABLE ONLY
        if isinstance(result, list):

            if len(result) <= 1:
                st.info("📭 No data found")

            else:
                try:
                    columns = result[0]
                    rows = result[1:]

                    df = pd.DataFrame(rows, columns=columns)
                    st.dataframe(df, use_container_width=True)

                except Exception:
                    st.error("Error displaying table")

        # ✅ ONLY IMPORTANT MESSAGES
        else:
            result_str = str(result)

            if "❌" in result_str or "error" in result_str.lower():
                st.error(result_str)

            elif "✅" in result_str:
                st.success(result_str)

            elif "⚠️" in result_str:
                st.warning(result_str)