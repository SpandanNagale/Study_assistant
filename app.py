import streamlit as st

# Page config
st.set_page_config(page_title="🤖 Unified AI Assistant", page_icon="🤖", layout="wide")
st.title("🤖 Unified AI Assistant")
st.caption("Switch between different AI tools with context-aware chat, summarization, coding help, and more!")

# --- Sidebar Navigation ---
bot_choice = st.sidebar.radio("Select an AI tool:", [
    "Multi Agents Chatbot",
    "PDF QA Bot",
    "Code Generator",
    "Debugger Chatbot",
    "Study Assistant",
    "PDF/Text Summarizer",
    "History-Aware Chatbot"
])

# Instructions
st.sidebar.markdown("---")
st.sidebar.subheader("💡 How to Use")
st.sidebar.markdown("""
- Select the tool from above.
- Follow the instructions for each bot.
- Use 'Clear Chat' if available to reset context.
""")

# --- Lazy loading of bots ---
if bot_choice == "Academic Assistant":
    from Agents import run_academic_assistant
    run_academic_assistant()

elif bot_choice == "PDF QA Bot":
    from pdf_qa_bot import run_pdf_qa_bot
    run_pdf_qa_bot()

elif bot_choice == "Code Generator":
    from code_generator import run_code_generator
    run_code_generator()

elif bot_choice == "Debugger Chatbot":
    from debugger_chatbot import run_debugger_chatbot
    run_debugger_chatbot()

elif bot_choice == "Study Assistant":
    from study_assistant import run_study_assistant
    run_study_assistant()

elif bot_choice == "PDF/Text Summarizer":
    from summarizer import run_summarizer
    run_summarizer()

elif bot_choice == "History-Aware Chatbot":
    from history_chatbot import run_history_chatbot
    run_history_chatbot()


