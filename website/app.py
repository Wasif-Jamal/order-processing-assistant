"""
Streamlit UI for the Order Processing Assistant.

Features
--------
* Wide layout.
* Persistent UUID session id.
* Chat interface.
* Displays SQL, source and explanation.
* Shows query results as a dataframe.
"""

from __future__ import annotations

import uuid

import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000/api/chat"

st.set_page_config(
    page_title="Order Processing Assistant",
    page_icon="📦",
    layout="wide",
)

st.title("📦 Order Processing Assistant")

# ---------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------

if "session_uuid" not in st.session_state:
    st.session_state.session_uuid = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------------------------------------------------------------
# Display chat history
# ---------------------------------------------------------------------

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

        if message["role"] == "assistant":
            if message.get("generated_sql"):
                with st.expander("Generated SQL"):
                    st.code(
                        message["generated_sql"],
                        language="sql",
                    )

            if message.get("sql_source"):
                st.caption(f"Source: **{message['sql_source']}**")

            if message.get("sql_explanation"):
                st.info(message["sql_explanation"])

            if message.get("query_result"):
                df = pd.DataFrame(
                    message["query_result"],
                    columns=message.get("columns"),
                )

                st.dataframe(
                    df,
                    use_container_width=True,
                )

                st.caption(f"{message.get('row_count', len(df))} rows")

            if message.get("error_message"):
                st.error(message["error_message"])

# ---------------------------------------------------------------------
# Chat Input
# ---------------------------------------------------------------------

if prompt := st.chat_input("Ask a question..."):
    st.session_state.messages.append(
        {
            "role": "user",
            "content": prompt,
        }
    )

    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()

        with st.spinner("Thinking..."):
            try:
                response = requests.post(
                    API_URL,
                    json={
                        "session_uuid": st.session_state.session_uuid,
                        "question": prompt,
                    },
                    timeout=120,
                )

                data = response.json()

            except Exception as ex:
                placeholder.error(str(ex))

                st.stop()

        assistant_text = ""

        if data.get("error_message"):
            assistant_text = data["error_message"]

        elif data.get("query_result") is not None:
            assistant_text = "Here are the results."

        else:
            assistant_text = data.get("sql_explanation") or "Done."

        placeholder.markdown(assistant_text)

        if data.get("generated_sql"):
            with st.expander("Generated SQL"):
                st.code(
                    data["generated_sql"],
                    language="sql",
                )

        if data.get("sql_source"):
            st.caption(f"Source: **{data['sql_source']}**")

        if data.get("sql_explanation"):
            st.info(data["sql_explanation"])

        if data.get("query_result"):
            df = pd.DataFrame(
                data["query_result"],
                columns=data.get("columns"),
            )

            st.dataframe(
                df,
                use_container_width=True,
            )

            st.caption(f"{data.get('row_count', len(df))} rows")

        if data.get("error_message"):
            st.error(data["error_message"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_text,
            "generated_sql": data.get("generated_sql"),
            "sql_source": data.get("sql_source"),
            "sql_explanation": data.get("sql_explanation"),
            "query_result": data.get("query_result"),
            "columns": data.get("columns"),
            "row_count": data.get("row_count"),
            "error_message": data.get("error_message"),
        }
    )
