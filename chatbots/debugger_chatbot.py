"""
Debugger Chatbot
----------------
Paste code + error message → get root cause analysis and fixes.
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


def run_debugger_chatbot():
    st.title("🐞 Debugger Chatbot")
    st.markdown("Paste your code and error message — get a detailed root cause analysis and fix.")

    llm = get_llm()

    # Session state for debug history
    if "debug_history" not in st.session_state:
        st.session_state.debug_history = []

    # Clear button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", key="clear_debug"):
            st.session_state.debug_history = []
            st.rerun()

    # Show history
    for entry in st.session_state.debug_history:
        with st.chat_message(entry["role"]):
            st.markdown(entry["content"])

    # Input form
    with st.form("debug_form", clear_on_submit=True):
        code = st.text_area("📋 Paste your code:", height=200, placeholder="def my_function():\n    ...")
        error = st.text_area("❌ Paste the error message:", height=100, placeholder="Traceback (most recent call last):\n    ...")
        submitted = st.form_submit_button("🔍 Debug", use_container_width=True)

    if submitted:
        if not code or not error:
            st.warning("Please provide both your code and the error message.")
            return

        user_content = f"**Code:**\n```\n{code}\n```\n\n**Error:**\n```\n{error}\n```"
        st.session_state.debug_history.append({"role": "user", "content": user_content})
        st.chat_message("user").markdown(user_content)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert software debugger. When given code and an error message:\n"
             "1. Identify the ROOT CAUSE of the error\n"
             "2. Explain WHY it happens in simple terms\n"
             "3. Provide the MINIMAL working fix with the corrected code\n"
             "4. Suggest any related best practices to prevent similar issues\n"
             "Format your response with clear sections using markdown."),
            ("user", "Code:\n{code}\n\nError:\n{error}"),
        ])

        chain = prompt | llm | StrOutputParser()

        with st.chat_message("assistant"):
            with st.spinner("🔍 Analyzing your code..."):
                try:
                    response = chain.invoke({"code": code, "error": error})
                    st.markdown(response)
                    st.session_state.debug_history.append({"role": "assistant", "content": response})
                except Exception as e:
                    error_msg = f"⚠️ Error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.debug_history.append({"role": "assistant", "content": error_msg})
