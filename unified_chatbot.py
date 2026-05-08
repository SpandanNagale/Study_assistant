"""
Unified Intelligent Chatbot
---------------------------
Single chat interface with intent-based routing to specialized handlers.
Automatically detects whether user needs: code generation, debugging, study help,
PDF analysis, summarization, academic research, or general conversation.
"""

import streamlit as st
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
import json
import re
from typing import Optional, Tuple
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'providers'))
from providers.llm_provider import get_llm


# ============================================================================
# Intent Detection
# ============================================================================

INTENT_CATEGORIES = {
    "code_generator": [
        "write code", "generate code", "create function", "implement",
        "code for", "programming", "script", "automation", "build me",
        "develop", "snippet", "algorithm", "class", "module"
    ],
    "debugger": [
        "error", "bug", "debug", "fix", "not working", "exception",
        "traceback", "crash", "issue", "problem with code", "why does this fail",
        "syntax error", "runtime error", "type error"
    ],
    "study_assistant": [
        "explain", "what is", "how does", "concept", "understand", "teach",
        "learn about", "tell me about", "definition", "meaning of",
        "how to understand", "break down", "simplify"
    ],
    "pdf_qa": [
        "in the pdf", "from the document", "in this file", "uploaded pdf",
        "according to the pdf", "document says", "file contains"
    ],
    "summarizer": [
        "summarize", "summary", "key points", "bullet points", "tl;dr",
        "main ideas", "condense", "brief", "overview of"
    ],
    "academic_research": [
        "research paper", "arxiv", "scientific", "academic", "scholarly",
        "peer-reviewed", "journal article", "citation", "pubmed", "wikipedia"
    ]
}

INTENT_PROMPT = """You are an intent classifier for a study assistant chatbot.
Analyze the user's query and classify it into ONE of these categories:

- code_generator: User wants code written or generated
- debugger: User has code with an error/bug to fix
- study_assistant: User wants to understand a concept or topic
- pdf_qa: User is asking about content from an uploaded PDF
- summarizer: User wants a summary of text/content
- academic_research: User is asking for research papers or academic sources
- general: General conversation that doesn't fit other categories

Consider the conversation history for context. If user references previous messages, maintain the same intent.

Return ONLY a JSON object with this format:
{{"intent": "category_name", "confidence": 0.0-1.0, "reason": "brief explanation"}}

User Query: {query}
Conversation History: {history}
"""


def detect_intent(query: str, history: list = None) -> Tuple[str, float]:
    """Detect the intent of a user query.

    Returns:
        Tuple of (intent_name, confidence_score)
    """
    # Quick keyword-based pre-check for common cases
    query_lower = query.lower()

    # Direct PDF references when PDFs are loaded
    if st.session_state.get("pdf_retriever") is not None:
        if any(kw in query_lower for kw in ["pdf", "document", "file", "uploaded"]):
            return "pdf_qa", 0.9

    # Check for code + error pattern (debugger)
    if any(kw in query_lower for kw in ["error", "bug", "exception", "traceback"]):
        if any(kw in query_lower for kw in ["code", "function", "script", "program"]):
            return "debugger", 0.85

    # Check for explicit code generation requests
    if any(phrase in query_lower for phrase in ["write code", "generate code", "create a", "create an", "make a", "make an"]):
        if any(kw in query_lower for kw in ["function", "program", "script", "app", "code", "class"]):
            return "code_generator", 0.85

    # Check for study/explanation requests
    if any(phrase in query_lower for phrase in ["explain", "what is", "how does", "tell me about", "what are"]):
        return "study_assistant", 0.8

    # Check for summary requests
    if any(phrase in query_lower for phrase in ["summarize", "give me a summary", "key points", "main points"]):
        return "summarizer", 0.85

    # For ambiguous cases, use LLM-based classification
    try:
        llm = get_llm()
        intent_prompt = ChatPromptTemplate.from_messages([
            ("system", INTENT_PROMPT),
        ])

        history_str = "\n".join([
            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
            for m in (history or [])[-4:]  # Last 4 messages for context
        ]) or "No previous conversation"

        chain = intent_prompt | llm | StrOutputParser()
        response = chain.invoke({
            "query": query,
            "history": history_str
        })

        # Parse JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
            intent = result.get("intent", "general")
            confidence = float(result.get("confidence", 0.5))
            return intent, confidence

    except Exception as e:
        # Fall back to keyword matching on error
        st.warning(f"Intent detection fallback: {e}")

    # Default to general
    return "general", 0.5


# ============================================================================
# Specialized Handlers
# ============================================================================

def handle_code_generator(query: str, history: list) -> str:
    """Generate code based on user request."""
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert code generation assistant.
        Write clean, correct, efficient, and well-documented code.
        - Always include comments explaining key logic
        - Use best practices and design patterns
        - Include error handling where appropriate
        - Format code in markdown code blocks with language specified
        - Explain your approach before showing code"""),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "history": history,
        "input": query
    })


def handle_debugger(query: str, history: list) -> str:
    """Debug code and provide fixes."""
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert software debugger.
        When given code and an error:
        1. Identify the ROOT CAUSE of the error
        2. Explain WHY it happens in simple terms
        3. Provide the MINIMAL working fix with corrected code
        4. Suggest best practices to prevent similar issues

        Format your response with clear sections using markdown.
        If the user didn't provide code, ask them to share it."""),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "history": history,
        "input": query
    })


def handle_study_assistant(query: str, history: list) -> str:
    """Explain concepts and provide educational guidance."""
    llm = get_llm()

    # Get user's standard/level from session
    standard = st.session_state.get("study_standard", "General")

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a personal study assistant and expert tutor.
        Your job:
        1. Break down concepts into simple, digestible parts
        2. Provide real-world examples and analogies
        3. Use step-by-step explanations
        4. Include key formulas, definitions, or code snippets when relevant
        5. End with 2-3 review questions to test understanding

        Adapt your explanation level to the student's standard/course: {standard or 'General'}
        """),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "history": history,
        "input": query
    })


def handle_pdf_qa(query: str, history: list) -> str:
    """Answer questions about uploaded PDFs."""
    from langchain.chains import create_history_aware_retriever, create_retrieval_chain
    from langchain.chains.combine_documents import create_stuff_documents_chain
    from langchain_community.chat_message_histories import ChatMessageHistory
    from langchain_core.chat_history import BaseChatMessageHistory
    from langchain_core.runnables.history import RunnableWithMessageHistory

    llm = get_llm()
    retriever = st.session_state.get("pdf_retriever")

    if retriever is None:
        return "I don't see any PDFs uploaded. Please upload a PDF file first, then I can answer questions about it."

    # Setup history-aware retrieval
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question, formulate a standalone question that can be understood without context."),
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

    response = rag_chain.invoke({
        "input": query,
        "chat_history": history
    })

    return response.get("answer", "I couldn't find an answer in the PDF.")


def handle_summarizer(query: str, history: list) -> str:
    """Summarize text or content."""
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert summarization assistant.
        Create comprehensive summaries that:
        - Capture all key points and main arguments
        - Include important details and evidence
        - Structure information with bullet points for clarity
        - Maintain the original meaning while being concise
        - Highlight any conclusions or actionable insights"""),
        MessagesPlaceholder("history"),
        ("human", "Please summarize the following:\n{input}"),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "history": history,
        "input": query
    })


def handle_academic_research(query: str, history: list) -> str:
    """Search academic sources (ArXiv, Wikipedia, PubMed, web)."""
    from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
    from langchain_community.tools import (
        ArxivQueryRun,
        WikipediaQueryRun,
        DuckDuckGoSearchResults,
        PubmedQueryRun,
    )
    from langchain.agents import initialize_agent, AgentType, Tool
    from langchain.agents.agent import AgentExecutor

    llm = get_llm()

    # Initialize tools
    arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(top_k_results=3, doc_content_chars_max=1000))
    wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=1000))
    pubmed = PubmedQueryRun()
    search = DuckDuckGoSearchResults(name="web_search")

    tools = [
        Tool(
            name="ArXiv",
            func=arxiv.run,
            description="Search for scientific papers on arXiv"
        ),
        Tool(
            name="Wikipedia",
            func=wiki.run,
            description="Search Wikipedia for general information"
        ),
        Tool(
            name="PubMed",
            func=pubmed.run,
            description="Search for biomedical papers on PubMed"
        ),
        Tool(
            name="WebSearch",
            func=search.run,
            description="Search the web for general information"
        ),
    ]

    from langchain.memory import ConversationBufferMemory
    from langchain_core.messages import HumanMessage, AIMessage

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    for msg in history:
        if isinstance(msg, HumanMessage):
            memory.chat_memory.add_user_message(msg.content)
        elif isinstance(msg, AIMessage):
            memory.chat_memory.add_ai_message(msg.content)

    # Create agent
    agent = initialize_agent(
        tools,
        llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        memory=memory,
        handle_parsing_errors=True,
        verbose=False,
    )

    try:
        response = agent.run(input=query)
        return response
    except Exception as e:
        return f"I encountered an issue while searching: {str(e)}. Let me try answering with my general knowledge instead."


def handle_general(query: str, history: list) -> str:
    """General conversation handler."""
    llm = get_llm()

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful, friendly AI study assistant.
        You have full context from the conversation history.
        Reference previous messages when relevant to provide consistent, contextual answers.
        Be encouraging and supportive of the student's learning journey."""),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])

    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "history": history,
        "input": query
    })


# ============================================================================
# Main Entry Point
# ============================================================================

def run_unified_chatbot():
    """Main unified chatbot interface with intelligent routing."""
    st.title("🤖 AI Study Assistant")
    st.markdown("Ask anything — I'll route your query to the right expert. Upload PDFs for document-specific questions.")

    # Initialize session state
    if "unified_chat_history" not in st.session_state:
        st.session_state.unified_chat_history = []
    if "study_standard" not in st.session_state:
        st.session_state.study_standard = ""
    if "pdf_retriever" not in st.session_state:
        st.session_state.pdf_retriever = None

    # Sidebar for settings
    with st.sidebar:
        st.markdown("### ⚙️ Settings")
        st.session_state.study_standard = st.text_input(
            "Your standard/course:",
            value=st.session_state.study_standard,
            placeholder="e.g., 12th Grade Physics, CS 101...",
            key="unified_standard_input",
        )

        st.markdown("---")
        st.markdown("### 📄 PDF Upload")
        uploaded_files = st.file_uploader(
            "Upload PDFs",
            type="pdf",
            accept_multiple_files=True,
            key="unified_pdf_uploader",
        )

        if uploaded_files:
            from langchain_text_splitters import RecursiveCharacterTextSplitter
            from langchain_community.vectorstores import FAISS
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.document_loaders import PyPDFLoader
            import tempfile
            import os

            if st.session_state.pdf_retriever is None:
                with st.spinner("📖 Processing PDFs..."):
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

                    if documents:
                        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
                        splits = text_splitter.split_documents(documents)
                        embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
                        vector_db = FAISS.from_documents(embedding=embeddings, documents=splits)
                        st.session_state.pdf_retriever = vector_db.as_retriever()
                        st.success(f"✅ Indexed {len(documents)} pages")

        st.markdown("---")
        if st.button("🗑️ Clear Chat & PDFs", key="clear_unified", use_container_width=True):
            st.session_state.unified_chat_history = []
            st.session_state.pdf_retriever = None
            st.session_state.pdf_store = {}
            st.rerun()

    # Show chat history
    for msg in st.session_state.unified_chat_history:
        if isinstance(msg, HumanMessage):
            with st.chat_message("user"):
                st.markdown(msg.content)
        else:
            with st.chat_message("assistant"):
                st.markdown(msg.content)

    # Chat input
    query = st.chat_input("Ask me anything...")

    if query:
        # Add user message
        user_msg = HumanMessage(content=query)
        st.session_state.unified_chat_history.append(user_msg)
        with st.chat_message("user"):
            st.markdown(query)

        # Detect intent
        with st.chat_message("assistant"):
            with st.spinner("🤔 Understanding your query..."):
                intent, confidence = detect_intent(query, st.session_state.unified_chat_history[:-1])

                # Show detected intent (subtle indicator)
                intent_emoji = {
                    "code_generator": "💻",
                    "debugger": "🐞",
                    "study_assistant": "📖",
                    "pdf_qa": "📄",
                    "summarizer": "📝",
                    "academic_research": "📚",
                    "general": "💬"
                }

                # Route to appropriate handler
                handlers = {
                    "code_generator": handle_code_generator,
                    "debugger": handle_debugger,
                    "study_assistant": handle_study_assistant,
                    "pdf_qa": handle_pdf_qa,
                    "summarizer": handle_summarizer,
                    "academic_research": handle_academic_research,
                    "general": handle_general,
                }

                handler = handlers.get(intent, handle_general)

                with st.spinner(f"{intent_emoji.get(intent, '💬')} Processing..."):
                    try:
                        # Convert history to LangChain format for handlers
                        history_msgs = st.session_state.unified_chat_history[:-1]
                        response = handler(query, history_msgs)

                        st.markdown(response)

                        # Add assistant response to history
                        st.session_state.unified_chat_history.append(AIMessage(content=response))

                    except Exception as e:
                        error_msg = f"⚠️ Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.unified_chat_history.append(AIMessage(content=error_msg))
