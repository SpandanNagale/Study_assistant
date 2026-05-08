"""
History-Aware Chatbot
--------------------
General-purpose AI assistant with full conversation memory.
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


def run_history_chatbot():
    st.title("💬 History-Aware Chatbot")
    st.markdown("AI assistant with full conversation memory — it remembers everything you've discussed.")

    llm = get_llm()

    # Session state
    if "history_messages" not in st.session_state:
        st.session_state.history_messages = []

    # Clear button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", key="clear_history"):
            st.session_state.history_messages = []
            st.rerun()

    # Show conversation history
    for msg in st.session_state.history_messages:
        if isinstance(msg, HumanMessage):
            st.chat_message("user").write(msg.content)
        else:
            st.chat_message("assistant").write(msg.content)

    # Prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a helpful, friendly AI assistant. "
         "You have full context from the conversation history. "
         "Reference previous messages when relevant to provide consistent, contextual answers."),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()

    # Chat input
    user_input = st.chat_input("Say something...")
    if user_input:
        st.session_state.history_messages.append(HumanMessage(content=user_input))
        st.chat_message("user").write(user_input)

        with st.chat_message("assistant"):
            with st.spinner("💭 Thinking..."):
                try:
                    response = chain.invoke({
                        "history": st.session_state.history_messages[:-1],
                        "input": user_input,
                    })
                    st.write(response)
                    st.session_state.history_messages.append(AIMessage(content=response))
                except Exception as e:
                    error_msg = f"⚠️ Error: {str(e)}"
                    st.error(error_msg)
