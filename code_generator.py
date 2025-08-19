import streamlit as st
from langchain.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain.memory import ConversationSummaryMemory
from langchain.chains import LLMChain
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

def run_code_generator():
    st.title("💻 Code Generator")
    st.write("Generate or improve code in any programming language with memory of previous tasks.")

    api_key = os.getenv("GROQ_API_KEY")
    llm = ChatGroq(model="llama3-8b-8192", api_key=api_key)

    general_template = """You are a code generation assistant.
    Write clean, correct, efficient code with explanations and comments if useful."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", general_template),
        ("human", "{input}")
    ])

    memory = ConversationSummaryMemory(llm=llm, return_messages=True)
    chain = LLMChain(llm=llm, prompt=prompt, memory=memory, output_parser=StrOutputParser())

    language = st.text_input("Programming Language:")
    task = st.text_area("Describe your task:")

    if st.button("Generate / Improve Code"):
        if language and task:
            user_input = f"Write {language} code for the following task:\n{task}"
            response = chain.run(input=user_input)
            st.subheader("✅ Generated Code:")
            st.code(response, language=language)
            st.sidebar.subheader("Conversation Summary")
            st.sidebar.write(memory.load_memory_variables({})["history"])
        else:
            st.warning("Please enter both language and task.")
