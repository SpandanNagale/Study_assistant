"""
PDF QA Bot
----------
Upload PDFs and ask questions about the content.
Uses FAISS vector store with history-aware retrieval.
"""

import streamlit as st
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import tempfile
import os
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


def run_pdf_qa_bot():
    st.title("📄 PDF Query Bot")
    st.markdown("Upload PDF(s) and ask questions — AI reads your documents and answers with context.")

    llm = get_llm()

    # Session state init
    if "pdf_store" not in st.session_state:
        st.session_state.pdf_store = {}
    if "pdf_session_id" not in st.session_state:
        st.session_state.pdf_session_id = "default_session"
    if "pdf_retriever" not in st.session_state:
        st.session_state.pdf_retriever = None
    if "pdf_chat_history" not in st.session_state:
        st.session_state.pdf_chat_history = []

    # Clear chat
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", key="clear_pdf"):
            st.session_state.pdf_store = {}
            st.session_state.pdf_retriever = None
            st.session_state.pdf_chat_history = []
            st.rerun()

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type="pdf",
        accept_multiple_files=True,
        key="pdf_uploader",
    )

    # Process PDFs only when new files are uploaded
    if uploaded_files and st.session_state.pdf_retriever is None:
        with st.spinner("📖 Reading and indexing your PDFs..."):
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
                    # Clean up temp file
                    if tmp_path and os.path.exists(tmp_path):
                        os.unlink(tmp_path)

            if documents:
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                splits = text_splitter.split_documents(documents)

                embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                vector_db = FAISS.from_documents(embedding=embeddings, documents=splits)
                st.session_state.pdf_retriever = vector_db.as_retriever()
                st.success(f"✅ Indexed {len(documents)} pages from {len(uploaded_files)} PDF(s)!")

    # Show chat history
    for msg in st.session_state.pdf_chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    # Chat functions
    def get_session_history(session: str) -> BaseChatMessageHistory:
        if session not in st.session_state.pdf_store:
            st.session_state.pdf_store[session] = ChatMessageHistory()
        return st.session_state.pdf_store[session]

    # Query input
    if st.session_state.pdf_retriever is not None:
        query = st.chat_input("Ask a question about your PDF(s)...")
        if query:
            st.session_state.pdf_chat_history.append({"role": "user", "content": query})
            st.chat_message("user").write(query)

            with st.chat_message("assistant"):
                with st.spinner("🤔 Thinking..."):
                    try:
                        retriever = st.session_state.pdf_retriever

                        contextualize_q_prompt = ChatPromptTemplate.from_messages([
                            ("system", "Given a chat history and the latest user question, formulate a standalone question."),
                            MessagesPlaceholder("chat_history"),
                            ("human", "{input}"),
                        ])
                        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

                        system_prompt = ChatPromptTemplate.from_messages([
                            ("system", "Use the retrieved context from the PDF to answer the question accurately. Quote relevant passages when helpful. If the answer is not in the PDF, say so clearly."),
                            MessagesPlaceholder("chat_history"),
                            ("human", "{input}"),
                        ])
                        question_answer_chain = create_stuff_documents_chain(llm, system_prompt)
                        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)

                        final_chain = RunnableWithMessageHistory(
                            rag_chain,
                            get_session_history,
                            input_messages_key="input",
                            history_messages_key="chat_history",
                            output_messages_key="answer",
                        )

                        response = final_chain.invoke(
                            {"input": query},
                            config={"configurable": {"session_id": st.session_state.pdf_session_id}},
                        )
                        answer = response["answer"]
                        st.write(answer)
                        st.session_state.pdf_chat_history.append({"role": "assistant", "content": answer})

                    except Exception as e:
                        error_msg = f"⚠️ Error processing query: {str(e)}"
                        st.error(error_msg)
                        st.session_state.pdf_chat_history.append({"role": "assistant", "content": error_msg})
    else:
        st.info("👆 Upload one or more PDFs above to start asking questions.")
