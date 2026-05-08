import streamlit as st
from providers.llm_provider import render_llm_sidebar

# ---------------------------------------------------------------------------
# Page config — MUST be the first Streamlit command
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="📚 Study Assistant — AI-Powered Learning Suite",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS for a premium look
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Global font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body {
        font-family: 'Inter', sans-serif;
    }
    
    /* Preserve Streamlit icon fonts */
    .stIcon, .material-symbols-rounded, [data-testid="stIconMaterial"] {
        font-family: 'Material Symbols Rounded' !important;
    }

    /* Main header gradient */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #8892b0;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] .stRadio label {
        color: #b0b0d0 !important;
    }

    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 500;
    }
    .badge-ready {
        background: rgba(46, 213, 115, 0.15);
        color: #2ed573;
        border: 1px solid rgba(46, 213, 115, 0.3);
    }
    .badge-new {
        background: rgba(102, 126, 234, 0.15);
        color: #667eea;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }

    /* Hide default Streamlit branding but keep header for sidebar toggle */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Navigation state — allows both sidebar and home page buttons to navigate
# ---------------------------------------------------------------------------
TOOLS = [
    "🏠 Home",
    "🤖 AI Assistant (Unified)",
    "🧠 Flashcard Generator",
    "❓ Quiz Generator",
]

# Initialize navigation state
if "nav_target" not in st.session_state:
    st.session_state.nav_target = "🏠 Home"



# ---------------------------------------------------------------------------
# Sidebar — Navigation + LLM Provider
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📚 Study Suite")
    sidebar_choice = st.radio(
        "Navigate:",
        TOOLS,
        index=TOOLS.index(st.session_state.nav_target),
        key="sidebar_nav",
        label_visibility="collapsed",
    )

# Sync sidebar selection to nav state
if sidebar_choice != st.session_state.nav_target:
    st.session_state.nav_target = sidebar_choice

bot_choice = st.session_state.nav_target

# LLM provider settings (rendered in sidebar)
render_llm_sidebar()

with st.sidebar:
    st.markdown("---")
    st.caption("Built with ❤️ for students")
    st.caption("v2.0 — Gemini · Groq · Ollama")


# ---------------------------------------------------------------------------
# Home Page
# ---------------------------------------------------------------------------
if bot_choice == "🏠 Home":
    st.markdown('<p class="main-header">📚 Study Assistant</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Your AI-powered learning suite — summarize, query, generate, and master any subject.</p>',
        unsafe_allow_html=True,
    )

    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    1. **Open the sidebar** (click the `>` arrow at top-left) to configure your LLM provider
    2. **Enter your API key** — Gemini is free & recommended, or use Ollama for local AI
    3. **Use the sidebar** to navigate to any tool!
    """)

    st.markdown("---")
    st.info("💡 **The Unified AI Assistant** combines all chat capabilities:\n- 📚 Academic Research (ArXiv, Wikipedia, PubMed)\n- 💻 Code Generation\n- 🐞 Debugging\n- 📖 Study Help\n- 📄 PDF Q&A\n- 📝 Summarization\n- 💬 General Chat\n\nJust ask your question and it will route to the right expert!")

    st.markdown("---")
    st.markdown("### 🔑 API Key Options")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown("""
        **🌐 Google Gemini (Recommended)**
        - Free tier available
        - Fast & capable
        - [Get API Key →](https://aistudio.google.com/apikey)
        """)
    with col_b:
        st.markdown("""
        **⚡ Groq**
        - Free tier available
        - Ultra-fast inference
        - [Get API Key →](https://console.groq.com)
        """)
    with col_c:
        st.markdown("""
        **🖥️ Ollama (Local)**
        - 100% free & private
        - Runs on your machine
        - [Download Ollama →](https://ollama.com)
        """)


# ---------------------------------------------------------------------------
# Tool pages — lazy import to avoid loading all modules
# ---------------------------------------------------------------------------
elif bot_choice == "🤖 AI Assistant (Unified)":
    from unified_chatbot import run_unified_chatbot
    run_unified_chatbot()

elif bot_choice == "🧠 Flashcard Generator":
    from chatbots.flashcard_generator import run_flashcard_generator
    run_flashcard_generator()

elif bot_choice == "❓ Quiz Generator":
    from chatbots.quiz_generator import run_quiz_generator
    run_quiz_generator()
