import streamlit as st
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_groq import ChatGroq
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import tempfile
import os
from dotenv import load_dotenv
load_dotenv()

def run_summarizer():
    st.title("📝 PDF/Text Summarizer")
    st.write("Summarize PDFs or raw text using AI.")

    api_key = os.getenv("GROQ_API_KEY")

    llm = ChatGroq(model="llama3-8b-8192", api_key=api_key)

    text_input = st.text_area("Paste text to summarize:")

    uploaded_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

    prompt = PromptTemplate(input_variables=["text"], template="Write a summary of the following text:\n{text}")

    if st.button("Summarize"):
        if text_input:
            chain = LLMChain(llm=llm, prompt=prompt)
            summary = chain.run({"text": text_input})
            st.subheader("Summary:")
            st.write(summary)
        elif uploaded_files:
            documents = []
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                loader = PyPDFLoader(tmp_path)
                pdf_docs = loader.load()
                documents.extend(pdf_docs)
            try:
                chain = load_summarize_chain(llm=llm, chain_type="stuff", prompt=prompt)
                output = chain.run(documents)
                st.subheader("PDF Summary:")
                st.write(output)
            except Exception:
                st.error("PDF too big, try splitting or different method.")
        else:
            st.warning("Provide text or upload PDFs.")
