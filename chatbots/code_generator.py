"""
Code Generator
--------------
Generate clean, documented code in any programming language.
Maintains conversation context within a session.
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


def run_code_generator():
    st.title("💻 Code Generator")
    st.markdown("Generate clean, documented code in any language with explanations.")

    llm = get_llm()

    # Session state
    if "codegen_history" not in st.session_state:
        st.session_state.codegen_history = []

    # Clear button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", key="clear_codegen"):
            st.session_state.codegen_history = []
            st.rerun()

    # Show chat history
    for msg in st.session_state.codegen_history:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        else:
            st.chat_message("assistant").write(msg.content)

    # Input form
    with st.form("codegen_form", clear_on_submit=True):
        col_lang, col_task = st.columns([1, 3])
        with col_lang:
            language = st.text_input("Language:", placeholder="Python, JavaScript, etc.")
        with col_task:
            task = st.text_area("Describe your task:", placeholder="e.g., Write a function that sorts a list using merge sort...")
        submitted = st.form_submit_button("🚀 Generate Code", use_container_width=True)

    if submitted:
        if not task:
            st.warning("Please describe what code you need.")
            return

        lang_str = language if language else "any appropriate language"
        user_input = f"Write {lang_str} code for the following task:\n{task}"

        st.session_state.codegen_history.append(HumanMessage(content=user_input))
        st.chat_message("user").write(user_input)

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert code generation assistant. "
             "Write clean, correct, efficient, well-documented code. "
             "Always include comments explaining key logic. "
             "Format code in proper markdown code blocks with the language specified."),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ])

        chain = prompt | llm | StrOutputParser()

        with st.chat_message("assistant"):
            with st.spinner("💻 Generating code..."):
                try:
                    response = chain.invoke({
                        "history": st.session_state.codegen_history[:-1],
                        "input": user_input,
                    })
                    st.markdown(response)
                    st.session_state.codegen_history.append(AIMessage(content=response))
                except Exception as e:
                    st.error(f"⚠️ Error generating code: {str(e)}")
