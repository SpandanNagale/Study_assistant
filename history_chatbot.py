import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_ollama import ChatOllama
from langchain.schema import HumanMessage, AIMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_groq import ChatGroq
import os 
from dotenv import load_dotenv
load_dotenv()

from state import get_history, add_message, get_memory

def run_history_chatbot():
    st.title("💬 History-Aware Chatbot")
    memory = get_memory()  # ConversationBufferMemory
    api_key = os.getenv("GROQ_API_KEY")

    def lc_history():
        msgs = []
        for m in memory.load_memory_variables({})["history"]:
            msgs.append(m)
        return msgs

    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful AI assistant. Keep context from previous conversation."),
        MessagesPlaceholder("history"),
        ("human", "{input}")
    ])

    llm = ChatGroq(model="llama3-8b-8192" , api_key=api_key)
    chain = ({"history": lambda _: lc_history(), "input": RunnablePassthrough()} | prompt | llm)

    if "rendered_idx" not in st.session_state:
        st.session_state.rendered_idx = 0

    def render_messages():
        history = get_history()
        new_msgs = history[st.session_state.rendered_idx:]
        for m in new_msgs:
            with st.chat_message("user" if m["role"]=="user" else "assistant"):
                st.markdown(m["content"])
        st.session_state.rendered_idx = len(history)

    render_messages()
    user_input = st.chat_input("Say something...")
    if user_input:
        ai_msg = chain.invoke(user_input)
        reply = getattr(ai_msg, "content", str(ai_msg))
        add_message("user", user_input)
        add_message("ai", reply)
        memory.save_context({"input": user_input}, {"output": reply})
        render_messages()

