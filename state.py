# state.py
import streamlit as st
from typing import List, Dict
from langchain.memory import ConversationBufferMemory

HISTORY_KEY = "history"
MEM_KEY = "memory"

def get_history() -> List[Dict[str, str]]:
    """Lazy init + return history list."""
    if HISTORY_KEY not in st.session_state:
        st.session_state[HISTORY_KEY] = []  # [{"role": "user"|"ai", "content": "..."}]
    return st.session_state[HISTORY_KEY]

def add_message(role: str, content: str) -> None:
    hist = get_history()
    hist.append({"role": role, "content": content})

def clear_history() -> None:
    if HISTORY_KEY in st.session_state:
        del st.session_state[HISTORY_KEY]

# state.py (continued)



def get_memory() -> ConversationBufferMemory:
    if MEM_KEY not in st.session_state:
        st.session_state[MEM_KEY] = ConversationBufferMemory(
            return_messages=True, memory_key="history"
        )
    return st.session_state[MEM_KEY]
