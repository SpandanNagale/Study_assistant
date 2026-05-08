"""
Multi-Agent Academic Assistant
------------------------------
Uses LangChain agents with ArXiv, Wikipedia, PubMed, and DuckDuckGo
to answer research and academic queries.
"""

import streamlit as st
from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities import ArxivAPIWrapper, WikipediaAPIWrapper
from langchain_community.tools import (
    ArxivQueryRun,
    WikipediaQueryRun,
    DuckDuckGoSearchResults,
    PubmedQueryRun,
)
from langchain_core.callbacks import BaseCallbackHandler
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'providers'))
from llm_provider import get_llm


class StreamlitStatusCallbackHandler(BaseCallbackHandler):
    """Custom callback that shows agent actions inside st.status."""

    def __init__(self, status_container):
        self.status = status_container
        self.current_tool = ""

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get("name", "Tool")
        self.current_tool = tool_name
        self.status.update(label=f"🔍 Searching {tool_name}...")
        self.status.write(f"**Query:** {input_str}")

    def on_tool_end(self, output, **kwargs):
        # Show a truncated preview of the tool output
        preview = output[:300] + "..." if len(output) > 300 else output
        self.status.write(f"**{self.current_tool} result:** {preview}")

    def on_agent_action(self, action, **kwargs):
        self.status.update(label=f"🤔 Thinking...")

    def on_agent_finish(self, finish, **kwargs):
        self.status.update(label="✅ Done!", state="complete")


def run_academic_assistant():
    st.title("📚 Multi Agent Research Chatbot")
    st.markdown("Ask research, math, or general academic queries — powered by multiple search agents.")

    llm = get_llm()

    # Initialize session state
    if "agent_messages" not in st.session_state:
        st.session_state.agent_messages = [
            {"role": "assistant", "content": "Hi! I'm your Academic Research Assistant 🤖\n\nI can search **ArXiv**, **Wikipedia**, **PubMed**, and the **web** to answer your questions. Try asking me about any research topic!"}
        ]

    # Clear chat button
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🗑️ Clear", key="clear_agent"):
            st.session_state.agent_messages = [
                {"role": "assistant", "content": "Chat cleared! Ask me anything 🤖"}
            ]
            st.rerun()

    # Show previous messages
    for msg in st.session_state.agent_messages:
        st.chat_message(msg["role"]).write(msg["content"])

    # Chat input
    query = st.chat_input("Enter your research question...")

    if query:
        # Add user message
        st.session_state.agent_messages.append({"role": "user", "content": query})
        st.chat_message("user").write(query)

        # Initialize tools
        arxiv = ArxivQueryRun(api_wrapper=ArxivAPIWrapper(top_k_results=2, doc_content_chars_max=500))
        wiki = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(top_k_results=2, doc_content_chars_max=500))
        pubmed = PubmedQueryRun()
        search = DuckDuckGoSearchResults(name="search")
        tools = [search, arxiv, wiki, pubmed]

        # Initialize agent
        search_agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            handle_parsing_errors=True,
        )

        with st.chat_message("assistant"):
            try:
                # Use st.status for clean progress display
                with st.status("🔍 Researching your question...", expanded=True) as status:
                    cb = StreamlitStatusCallbackHandler(status)
                    response = search_agent.run(query, callbacks=[cb])
                    status.update(label="✅ Research complete!", state="complete", expanded=False)

                # Display the final answer cleanly
                st.markdown(response)
                st.session_state.agent_messages.append({"role": "assistant", "content": response})

            except Exception as e:
                error_msg = f"⚠️ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.agent_messages.append({"role": "assistant", "content": error_msg})
