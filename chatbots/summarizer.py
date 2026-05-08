"""
PDF/Text Summarizer
-------------------
Summarize PDFs or raw text using AI.
Supports large PDFs via map-reduce chain.
"""

import streamlit as st
from langchain_core.prompts import PromptTemplate
from langchain.chains.summarize import load_summarize_chain
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
import tempfile
import os
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


def run_summarizer():
    st.title("📝 PDF/Text Summarizer")
    st.markdown("Summarize PDFs or raw text into concise, actionable notes.")

    llm = get_llm()

    # Tabs for text vs PDF
    tab_text, tab_pdf = st.tabs(["📝 Text Input", "📄 PDF Upload"])

    prompt_template = PromptTemplate(
        input_variables=["text"],
        template=(
            "Write a comprehensive summary of the following text. "
            "Include key points, main arguments, and important details. "
            "Structure the summary with bullet points for clarity:\n\n{text}"
        ),
    )

    with tab_text:
        text_input = st.text_area(
            "Paste text to summarize:",
            height=250,
            placeholder="Paste your text, notes, or article here...",
        )
        if st.button("📝 Summarize Text", key="summarize_text", use_container_width=True):
            if not text_input:
                st.warning("Please paste some text to summarize.")
                return
            with st.spinner("✍️ Generating summary..."):
                try:
                    doc = Document(page_content=text_input)
                    chain = load_summarize_chain(llm=llm, chain_type="stuff", prompt=prompt_template)
                    output = chain.invoke([doc])
                    summary = output.get("output_text", str(output))
                    st.subheader("📋 Summary:")
                    st.markdown(summary)

                    # Download button
                    st.download_button(
                        "⬇️ Download Summary",
                        data=summary,
                        file_name="summary.md",
                        mime="text/markdown",
                    )
                except Exception as e:
                    st.error(f"⚠️ Error summarizing: {str(e)}")

    with tab_pdf:
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type="pdf",
            accept_multiple_files=True,
            key="summarizer_pdf_uploader",
        )
        if st.button("📄 Summarize PDFs", key="summarize_pdf", use_container_width=True):
            if not uploaded_files:
                st.warning("Please upload at least one PDF.")
                return

            with st.spinner("📖 Reading and summarizing PDFs..."):
                try:
                    documents = []
                    for uploaded_file in uploaded_files:
                        tmp_path = None
                        try:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                                tmp.write(uploaded_file.getvalue())
                                tmp_path = tmp.name
                            loader = PyPDFLoader(tmp_path)
                            pdf_docs = loader.load()
                            documents.extend(pdf_docs)
                        finally:
                            if tmp_path and os.path.exists(tmp_path):
                                os.unlink(tmp_path)

                    if not documents:
                        st.warning("No content could be extracted from the PDFs.")
                        return

                    # Use map_reduce for large PDFs, stuff for small ones
                    total_chars = sum(len(doc.page_content) for doc in documents)
                    chain_type = "map_reduce" if total_chars > 10000 else "stuff"

                    st.info(f"📊 Processing {len(documents)} pages ({total_chars:,} characters) using {chain_type} strategy...")

                    chain = load_summarize_chain(llm=llm, chain_type=chain_type)
                    output = chain.invoke(documents)
                    summary = output.get("output_text", str(output))

                    st.subheader("📋 PDF Summary:")
                    st.markdown(summary)

                    # Download button
                    st.download_button(
                        "⬇️ Download Summary",
                        data=summary,
                        file_name="pdf_summary.md",
                        mime="text/markdown",
                    )
                except Exception as e:
                    st.error(f"⚠️ Error summarizing PDFs: {str(e)}")
