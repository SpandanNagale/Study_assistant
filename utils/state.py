"""
State Management
----------------
Centralized session state helpers for chat history and memory.
"""

import streamlit as st
from typing import List, Dict

HISTORY_KEY = "history"


def get_history() -> List[Dict[str, str]]:
    """Get or initialize the chat history list."""
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []
    return st.session_state[HISTORY_KEY]


def add_message(role: str, content: str) -> None:
    """Add a message to chat history."""
    hist = get_history()
    hist.append({"role": role, "content": content})


def clear_history() -> None:
    """Clear the chat history."""
    if HISTORY_KEY in st.session_state:
        del st.session_state[HISTORY_KEY]
