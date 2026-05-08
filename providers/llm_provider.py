"""
LLM Provider Module
-------------------
Centralizes LLM initialization across all modules.
Supports: Gemini (free), Groq (free tier), and Ollama (local).
Users can enter their API key in the sidebar or use .env file.
"""

import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider constants
# ---------------------------------------------------------------------------
PROVIDERS = {
    "Gemini (Free - Recommended)": "gemini",
    "Groq (Free Tier)": "groq",
    "Ollama (Local LLM)": "ollama",
}

GEMINI_MODELS = [
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite",
    "gemini-1.5-pro",
]

GROQ_MODELS = [
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]

OLLAMA_MODELS = [
    "llama3",
    "llama3.1",
    "mistral",
    "phi3",
    "gemma4:latest",
    "qwen2",
]


# ---------------------------------------------------------------------------
# Sidebar UI for provider selection + API key input
# ---------------------------------------------------------------------------
def render_llm_sidebar():
    """Render the LLM provider selection UI in the Streamlit sidebar.
    
    Returns a dict with provider, model, and api_key info stored 
    in st.session_state so it persists across reruns.
    """
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔑 LLM Provider Settings")

        # Provider selector
        provider_label = st.selectbox(
            "Choose LLM Provider:",
            list(PROVIDERS.keys()),
            index=0,
            key="llm_provider_select",
        )
        provider = PROVIDERS[provider_label]

        # --- Provider-specific UI ---
        if provider == "gemini":
            env_key = os.getenv("GEMINI_API_KEY", "")
            api_key = st.text_input(
                "Gemini API Key:",
                value=env_key,
                type="password",
                help="Get a free key at https://aistudio.google.com/apikey",
                key="gemini_api_key_input",
            )
            if not api_key:
                st.info("🔗 [Get a free Gemini API key](https://aistudio.google.com/apikey)")
            model = st.selectbox("Gemini Model:", GEMINI_MODELS, key="gemini_model_select")

        elif provider == "groq":
            env_key = os.getenv("GROQ_API_KEY", "")
            api_key = st.text_input(
                "Groq API Key:",
                value=env_key,
                type="password",
                help="Get a free key at https://console.groq.com",
                key="groq_api_key_input",
            )
            if not api_key:
                st.info("🔗 [Get a free Groq API key](https://console.groq.com)")
            model = st.selectbox("Groq Model:", GROQ_MODELS, key="groq_model_select")

        elif provider == "ollama":
            api_key = None
            model = st.selectbox("Ollama Model:", OLLAMA_MODELS, key="ollama_model_select")
            ollama_url = st.text_input(
                "Ollama Server URL:",
                value="http://localhost:11434",
                key="ollama_url_input",
            )
            st.info("📦 Make sure Ollama is running locally. [Download Ollama](https://ollama.com)")
            st.session_state["ollama_url"] = ollama_url

        # Store in session state
        st.session_state["llm_provider"] = provider
        st.session_state["llm_model"] = model
        st.session_state["llm_api_key"] = api_key

        return {"provider": provider, "model": model, "api_key": api_key}


# ---------------------------------------------------------------------------
# LLM Factory
# ---------------------------------------------------------------------------
def get_llm():
    """Create and return the configured LLM instance.
    
    Raises a user-friendly error if API key is missing for cloud providers.
    """
    provider = st.session_state.get("llm_provider", "gemini")
    model = st.session_state.get("llm_model", "gemini-2.0-flash")
    api_key = st.session_state.get("llm_api_key", "")

    try:
        if provider == "gemini":
            if not api_key:
                st.error("⚠️ Please enter your Gemini API key in the sidebar.")
                st.stop()
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=api_key,
                temperature=0.7,
            )

        elif provider == "groq":
            if not api_key:
                st.error("⚠️ Please enter your Groq API key in the sidebar.")
                st.stop()
            from langchain_groq import ChatGroq
            return ChatGroq(model=model, api_key=api_key)

        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            ollama_url = st.session_state.get("ollama_url", "http://localhost:11434")
            return ChatOllama(
                model=model,
                base_url=ollama_url,
            )

    except ImportError as e:
        missing = str(e).split("'")[-2] if "'" in str(e) else str(e)
        st.error(
            f"⚠️ Missing dependency for {provider}: `{missing}`.\n\n"
            f"Install it with: `pip install {missing}`"
        )
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Failed to initialize LLM: {str(e)}")
        st.stop()
