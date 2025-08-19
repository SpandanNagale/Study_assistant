import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain.schema import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
load_dotenv()

def run_study_assistant():
    st.set_page_config(page_title="📚 Study Assistant", page_icon="📚")
    st.title("📚 AI Study Assistant")
    st.write("Get detailed explanations and learning guidance for any concept.")

    api_key = os.getenv("GROQ_API_KEY")

    llm = ChatGroq(model="llama3-8b-8192", api_key=api_key)

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "standard" not in st.session_state:
        st.session_state.standard = ""

    with st.sidebar:
        st.header("📖 Course Info")
        st.session_state.standard = st.text_input("Enter your standard/course:", value=st.session_state.standard)
        st.markdown("---")

    def study_assistant_chain(concept, standard):
        general_template = """You are a personal study assistant. Break down topics, give examples, and guide toward mastery."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", general_template),
            MessagesPlaceholder("history"),
            ("user", "Concept: {concept}\nStandard/Course: {standard}")
        ])
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({"history": st.session_state.chat_history, "concept": concept, "standard": standard})

    # Show past messages
    for msg in st.session_state.chat_history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg.content)

    # Chat input
    if prompt_text := st.chat_input("Ask about a concept..."):
        st.session_state.chat_history.append(HumanMessage(content=f"Concept: {prompt_text}\nStandard: {st.session_state.standard}"))
        with st.chat_message("user"):
            st.markdown(prompt_text)
        response = study_assistant_chain(prompt_text, st.session_state.standard)
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state.chat_history.append(AIMessage(content=response))
