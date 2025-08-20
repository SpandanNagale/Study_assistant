import streamlit as st
from langchain.agents import initialize_agent, AgentType
from langchain_groq import ChatGroq
from langchain.utilities import ArxivAPIWrapper, WikipediaAPIWrapper, WolframAlphaAPIWrapper
from langchain_community.tools import (
    ArxivQueryRun,
    WikipediaQueryRun,
    DuckDuckGoSearchResults,
    PubmedQueryRun,
    WolframAlphaQueryRun
)
from langchain_experimental.tools import PythonREPLTool
from langchain.callbacks import StreamlitCallbackHandler
import os
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

def run_academic_assistant():
    st.title("📚 Multi Agents Chatbot")
    st.write("Ask research, math, or general queries!")

    api_key = os.getenv("GROQ_API_KEY")


    llm = ChatGroq(model="llama3-8b-8192", api_key=api_key)

    query = st.chat_input("Enter your question:")

    if query:
        # Initialize tools
        arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500))
        wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500))
        pubmed = PubmedQueryRun()
        search = DuckDuckGoSearchResults(name="search")
        

        tools = [search, arxiv, wiki, pubmed]

        if "messages" not in st.session_state:
            st.session_state.messages = [
                {"role": "assistant", "content": "Hi! I'm your Academic Assistant 🤖"}
            ]

        # Show previous messages
        for msg in st.session_state.messages:
            st.chat_message(msg["role"]).write(msg["content"])

        # Add user query
        st.session_state.messages.append({"role": "user", "content": query})
        st.chat_message("user").write(query)

        # Initialize agent
        search_agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True
        )

        with st.chat_message("assistant"):
            st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
            response = search_agent.run(query, callbacks=[st_cb])
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.write(response)

