"""
LLM Provider Module
-------------------
Centralizes LLM initialization across all modules.

Supported providers:
  - Gemini        (Google AI Studio, free tier)
  - Groq          (free tier, very fast)
  - OpenRouter    (one key, hundreds of models incl. free ones)
  - Ollama Cloud  (hosted Ollama models at ollama.com, API key)
  - Ollama Local  (runs on your machine, no key)

Keys are read from (in order): the sidebar input, Streamlit secrets, the .env file.
When "Auto-fallback" is on, every other provider that has a key configured is
chained behind the primary one, so a rate limit or outage on one provider
transparently retries on the next.
"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------
# Model lists are suggestions; every provider also accepts a custom model id.
PROVIDERS = {
    "gemini": {
        "label": "Gemini (Free - Recommended)",
        "env_key": "GEMINI_API_KEY",
        "key_url": "https://aistudio.google.com/apikey",
        "models": [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.5-pro",
            "gemini-2.0-flash",
        ],
    },
    "groq": {
        "label": "Groq (Free Tier, Ultra-fast)",
        "env_key": "GROQ_API_KEY",
        "key_url": "https://console.groq.com/keys",
        "models": [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "openai/gpt-oss-120b",
            "openai/gpt-oss-20b",
            "qwen/qwen3-32b",
            "moonshotai/kimi-k2-instruct",
        ],
    },
    "openrouter": {
        "label": "OpenRouter (Many Models)",
        "env_key": "OPENROUTER_API_KEY",
        "key_url": "https://openrouter.ai/keys",
        "models": [
            "meta-llama/llama-3.3-70b-instruct:free",
            "deepseek/deepseek-chat-v3-0324:free",
            "openai/gpt-oss-20b:free",
            "qwen/qwen3-coder:free",
            "openrouter/auto",
        ],
    },
    "ollama_cloud": {
        "label": "Ollama Cloud",
        "env_key": "OLLAMA_API_KEY",
        "key_url": "https://ollama.com/settings/keys",
        "models": [
            "gpt-oss:120b",
            "gpt-oss:20b",
            "deepseek-v3.1:671b",
            "qwen3-coder:480b",
            "kimi-k2:1t",
        ],
    },
    "ollama": {
        "label": "Ollama (Local LLM)",
        "env_key": None,
        "key_url": "https://ollama.com/download",
        "models": [
            "llama3.1",
            "llama3.2",
            "qwen2.5",
            "mistral",
            "phi3",
            "gemma3",
        ],
    },
}

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OLLAMA_CLOUD_URL = "https://ollama.com"
DEFAULT_OLLAMA_URL = "http://localhost:11434"
CUSTOM_MODEL_OPTION = "✏️ Custom model..."

# Order in which fallback providers are tried after the primary one.
FALLBACK_ORDER = ["gemini", "groq", "openrouter", "ollama_cloud"]


def _secret(name):
    """Read a key from Streamlit secrets (if configured) or the environment."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        # No secrets.toml present
        pass
    return os.getenv(name, "")


def get_api_key(provider):
    """Return the API key for a provider: sidebar input first, then secrets/.env."""
    env_key = PROVIDERS[provider]["env_key"]
    if not env_key:
        return None
    return st.session_state.get(f"api_key_{provider}") or _secret(env_key)


def configured_providers():
    """Cloud providers that currently have an API key available."""
    return [p for p in FALLBACK_ORDER if get_api_key(p)]


# ---------------------------------------------------------------------------
# Sidebar UI for provider selection + API key input
# ---------------------------------------------------------------------------
def render_llm_sidebar():
    """Render the LLM provider selection UI in the Streamlit sidebar.

    Stores provider/model choices in st.session_state so they persist across reruns.
    """
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔑 LLM Provider Settings")

        # --- API keys (one per provider, pre-filled from secrets/.env) ---
        with st.expander("API Keys", expanded=not configured_providers()):
            for pid in FALLBACK_ORDER:
                cfg = PROVIDERS[pid]
                st.text_input(
                    f"{cfg['label'].split(' (')[0]} API Key:",
                    value=_secret(cfg["env_key"]),
                    type="password",
                    help=f"Get a key at {cfg['key_url']}",
                    key=f"api_key_{pid}",
                )
            ready = configured_providers()
            if ready:
                st.caption("✅ Keys set: " + ", ".join(PROVIDERS[p]["label"].split(" (")[0] for p in ready))

        # --- Primary provider + model ---
        provider_ids = list(PROVIDERS.keys())
        provider = st.selectbox(
            "Primary provider:",
            provider_ids,
            format_func=lambda p: PROVIDERS[p]["label"],
            key="llm_provider_select",
        )
        cfg = PROVIDERS[provider]

        model_choice = st.selectbox(
            "Model:",
            cfg["models"] + [CUSTOM_MODEL_OPTION],
            key=f"{provider}_model_select",
        )
        if model_choice == CUSTOM_MODEL_OPTION:
            model = st.text_input(
                "Custom model id:",
                key=f"{provider}_custom_model",
                placeholder=cfg["models"][0],
            ).strip() or cfg["models"][0]
        else:
            model = model_choice

        if provider == "ollama":
            st.session_state["ollama_url"] = st.text_input(
                "Ollama Server URL:",
                value=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_URL),
                key="ollama_url_input",
            )
            st.info("📦 Make sure Ollama is running locally. [Download Ollama](https://ollama.com)")
        elif not get_api_key(provider):
            st.info(f"🔗 [Get a {cfg['label'].split(' (')[0]} API key]({cfg['key_url']}) and paste it under **API Keys**.")

        st.toggle(
            "🛟 Auto-fallback to other providers",
            value=True,
            key="llm_auto_fallback",
            help="If the primary provider fails (rate limit, outage, bad model), "
                 "retry automatically with the other providers that have keys.",
        )

        # Store in session state
        st.session_state["llm_provider"] = provider
        st.session_state["llm_model"] = model
        st.session_state["llm_api_key"] = get_api_key(provider)

        return {"provider": provider, "model": model, "api_key": st.session_state["llm_api_key"]}


# ---------------------------------------------------------------------------
# LLM Factory
# ---------------------------------------------------------------------------
def build_llm(provider, model=None, api_key=None, temperature=0.7):
    """Construct a chat model for the given provider. Raises on missing key/deps."""
    cfg = PROVIDERS[provider]
    model = model or cfg["models"][0]
    if cfg["env_key"] and not api_key:
        raise ValueError(f"No API key configured for {cfg['label']}.")

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, google_api_key=api_key, temperature=temperature)

    if provider == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(model=model, api_key=api_key, temperature=temperature)

    if provider == "openrouter":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=model,
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL,
            temperature=temperature,
            default_headers={
                # Optional attribution headers recommended by OpenRouter
                "HTTP-Referer": "https://github.com/SpandanNagale/Study_assistant",
                "X-Title": "Study Assistant",
            },
        )

    if provider == "ollama_cloud":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=model,
            base_url=OLLAMA_CLOUD_URL,
            temperature=temperature,
            client_kwargs={"headers": {"Authorization": f"Bearer {api_key}"}},
        )

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        base_url = st.session_state.get("ollama_url", DEFAULT_OLLAMA_URL)
        return ChatOllama(model=model, base_url=base_url, temperature=temperature)

    raise ValueError(f"Unknown provider: {provider}")


def get_llm():
    """Create and return the configured LLM instance (with fallbacks if enabled).

    Stops the Streamlit script with a user-friendly error if nothing is usable.
    """
    provider = st.session_state.get("llm_provider", "gemini")
    model = st.session_state.get("llm_model") or PROVIDERS[provider]["models"][0]

    try:
        primary = build_llm(provider, model, get_api_key(provider))
    except ImportError as e:
        missing = getattr(e, "name", None) or str(e)
        st.error(
            f"⚠️ Missing dependency for {PROVIDERS[provider]['label']}: `{missing}`.\n\n"
            "Install it with: `pip install -r requirements.txt`"
        )
        st.stop()
    except ValueError:
        # Primary has no key — fall back to the first configured provider, if any.
        others = configured_providers()
        if not others:
            st.error("⚠️ Please enter an API key in the sidebar under **🔑 LLM Provider Settings → API Keys**.")
            st.stop()
        provider, primary = others[0], build_llm(others[0], None, get_api_key(others[0]))
        st.toast(f"Using {PROVIDERS[provider]['label']} (no key for the selected provider).")
    except Exception as e:
        st.error(f"⚠️ Failed to initialize LLM: {e}")
        st.stop()

    if not st.session_state.get("llm_auto_fallback", True):
        return primary

    fallbacks = []
    for pid in configured_providers():
        if pid == provider:
            continue
        try:
            fallbacks.append(build_llm(pid, None, get_api_key(pid)))
        except Exception:
            # A broken fallback should never block the primary provider.
            continue

    return primary.with_fallbacks(fallbacks) if fallbacks else primary
