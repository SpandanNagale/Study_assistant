"""
Study Assistant
---------------
AI tutor that breaks down concepts, provides examples,
and guides students toward mastery. Context-aware within a session.
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages import HumanMessage, AIMessage
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


def run_study_assistant():
    st.title("📖 AI Study Assistant")
    st.markdown("Get detailed explanations, examples, and study guidance for any concept.")

    llm = get_llm()

    # Session state
    if "study_chat_history" not in st.session_state:
        st.session_state.study_chat_history = []
    if "study_standard" not in st.session_state:
        st.session_state.study_standard = ""

    # Sidebar for course info
    with st.sidebar:
        st.markdown("---")
        st.subheader("📖 Course Info")
        st.session_state.study_standard = st.text_input(
            "Your standard/course:",
            value=st.session_state.study_standard,
            placeholder="e.g., 12th Grade Physics, CS 101, MBA Finance...",
            key="study_standard_input",
        )

    # Clear chat button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", key="clear_study"):
            st.session_state.study_chat_history = []
            st.rerun()

    # Show past messages
    for msg in st.session_state.study_chat_history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg.content)

    # Study assistant chain
    def study_chain(concept, standard):
        system_msg = (
            "You are a personal study assistant and expert tutor. Your job:\n"
            "1. Break down the concept into simple, digestible parts\n"
            "2. Provide real-world examples and analogies\n"
            "3. Use step-by-step explanations\n"
            "4. Include key formulas, definitions, or code snippets when relevant\n"
            "5. End with 2-3 review questions to test understanding\n"
            "Adapt your explanation level to the student's standard/course."
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_msg),
            MessagesPlaceholder("history"),
            ("user", "Concept: {concept}\nStudent Level: {standard}"),
        ])

        chain = prompt | llm | StrOutputParser()
        return chain.invoke({
            "history": st.session_state.study_chat_history,
            "concept": concept,
            "standard": standard or "General",
        })

    # Chat input
    if prompt_text := st.chat_input("Ask about any concept... (e.g., 'Explain photosynthesis')"):
        st.session_state.study_chat_history.append(
            HumanMessage(content=f"Concept: {prompt_text}\nLevel: {st.session_state.study_standard or 'General'}")
        )
        with st.chat_message("user"):
            st.markdown(prompt_text)

        with st.chat_message("assistant"):
            with st.spinner("📚 Preparing your explanation..."):
                try:
                    response = study_chain(prompt_text, st.session_state.study_standard)
                    st.markdown(response)
                    st.session_state.study_chat_history.append(AIMessage(content=response))
                except Exception as e:
                    st.error(f"⚠️ Error: {str(e)}")
