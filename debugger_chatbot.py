import streamlit as st
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
load_dotenv()

def run_debugger_chatbot():
    st.title("🐞 Debugger Chatbot")
    st.write("Paste your code and error; get a detailed fix.")

    api_key = os.getenv("GROQ_API_KEY")

    llm = ChatGroq(model="llama3-8b-8192", api_key=api_key)

    code = st.text_area("Paste your full code here:")
    error = st.text_area("Paste the error message:")

    if st.button("Submit"):
        if code and error:
            general_template = """You are an expert software debugger. Identify the root cause, explain it, and provide minimal working fixes."""
            prompt = ChatPromptTemplate.from_messages([
                ("system", general_template),
                ("user", "Code: {code}"),
                ("user", "Error: {error}")
            ])
            chain = prompt | llm | StrOutputParser()
            response = chain.invoke({"code": code, "error": error})
            st.subheader("💡 Suggested Fix:")
            st.write(response)
        else:
            st.warning("Please provide both code and error message.")
