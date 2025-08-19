import streamlit as st
from langchain_groq import ChatGroq
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
import tempfile
import os
from dotenv import load_dotenv
load_dotenv()

def run_pdf_qa_bot():
    st.title("📄 PDF Query Bot")
    st.write("Upload PDF(s) and ask questions about the content.")

    if "store" not in st.session_state:
        st.session_state.store = {}
    if "session_id" not in st.session_state:
        st.session_state.session_id = "default_session"

    api_key =os.getenv("GROQ_API_KEY")

    llm = ChatGroq(model="llama3-8b-8192", api_key=api_key)

    def loader():
        uploaded_files = st.file_uploader(
            "Upload PDF files", 
            type="pdf", 
            accept_multiple_files=True
        )
        documents = []
        if uploaded_files:
            for uploaded_file in uploaded_files:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(uploaded_file.getvalue())
                    tmp_path = tmp.name
                loader = PyPDFLoader(tmp_path)
                pdf_docs = loader.load()
                documents.extend(pdf_docs)
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        return text_splitter.split_documents(documents)

    def vec_DB(docs):
        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        vector_DB = FAISS.from_documents(embedding=embeddings, documents=docs)
        retriever = vector_DB.as_retriever()
        return retriever

    def get_session_history(session:str)->BaseChatMessageHistory:
        if st.session_state.session_id not in st.session_state.store:
            st.session_state.store[st.session_state.session_id] = ChatMessageHistory()
        return st.session_state.store[st.session_state.session_id]

    def retrieval_chain(input, retriever, llm):
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question, "
            "formulate a standalone question which can be understood without the chat history."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [("system", contextualize_q_system_prompt),
             MessagesPlaceholder("chat_history"),
             ("human","{input}")]
        )
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
        system_prompt = ChatPromptTemplate(
            [("system", "Use the retrieved context to answer the question. {context}"),
             MessagesPlaceholder("chat_history"),
             ("human", "{input}")]
        )
        question_answer_chain = create_stuff_documents_chain(llm, system_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
        final_chain = RunnableWithMessageHistory(rag_chain, get_session_history, input_messages_key="input", history_messages_key="chat_history", output_messages_key="answer")
        response = final_chain.invoke({"input": input}, config={"configurable": {"session_id": st.session_state.session_id}})
        st.write(response["answer"])

    docs = loader()
    if docs:
        retriever = vec_DB(docs)
        query = st.text_input("Enter your question about PDF(s):")
        if query:
            retrieval_chain(query, retriever, llm)


