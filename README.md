# 📚 Study Assistant — AI-Powered Learning Suite

A comprehensive AI study assistant built with **LangChain** and **Streamlit**.  
Supports **Google Gemini** (free), **Groq** (free tier), and **Ollama** (local LLM).

> 🎓 Summarize documents, ask questions about PDFs, generate code, debug errors, create flashcards, take quizzes, and more — all powered by AI.

---

## ✨ Features

| Tool | Description |
|------|-------------|
| 📚 **Multi Agent Chatbot** | Research assistant with ArXiv, Wikipedia, PubMed, and web search |
| 📄 **PDF QA Bot** | Upload PDFs and ask questions with context-aware answers |
| 💻 **Code Generator** | Generate documented code in any programming language |
| 🐞 **Debugger Chatbot** | Paste code + error → get root cause analysis and fixes |
| 📖 **Study Assistant** | AI tutor that breaks down concepts with examples |
| 📝 **PDF/Text Summarizer** | Summarize PDFs or text with download support |
| 💬 **History-Aware Chatbot** | General AI assistant with full conversation memory |
| 🧠 **Flashcard Generator** | Create spaced-repetition flashcards from topics or PDFs |
| ❓ **Quiz Generator** | Auto-generate MCQ quizzes with scoring and explanations |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- One of the following:
  - **Google Gemini API key** (free) — [Get one here](https://aistudio.google.com/apikey)
  - **Groq API key** (free tier) — [Get one here](https://console.groq.com)
  - **Ollama installed locally** (100% free, no API key needed) — [Download](https://ollama.com)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/SpandanNagale/Study_assistant.git
cd Study_assistant

# 2. Create a virtual environment
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Copy and fill in your API keys
cp .env.example .env
# Edit .env with your keys, OR enter them directly in the app sidebar

# 5. Run the app
streamlit run app.py
```

The app will open at `http://localhost:8501`.

---

## 🔑 LLM Provider Options

You can choose your LLM provider directly in the app sidebar:

### Option 1: Google Gemini (Recommended for beginners)
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Paste the key in the app sidebar

### Option 2: Groq (Ultra-fast inference)
1. Go to [Groq Console](https://console.groq.com)
2. Sign up for a free account
3. Create an API key
4. Paste the key in the app sidebar

### Option 3: Ollama (100% Local & Private)
1. [Download and install Ollama](https://ollama.com)
2. Pull a model: `ollama pull llama3`
3. Start Ollama (it runs in the background)
4. Select "Ollama (Local LLM)" in the app sidebar
5. No API key needed!

---

## 📁 Project Structure

```
Study_assistant/
├── app.py                  # Main entry point with navigation and UI
├── llm_provider.py         # Centralized LLM provider (Gemini/Groq/Ollama)
├── agents.py               # Multi-agent research chatbot
├── pdf_qa_bot.py           # PDF question-answering with RAG
├── code_generator.py       # AI code generation
├── debugger_chatbot.py     # Code debugging assistant
├── study_assistant.py      # Study tutor with concept breakdown
├── summarizer.py           # PDF/text summarization
├── history_chatbot.py      # History-aware general chatbot
├── flashcard_generator.py  # Flashcard generation from topics/PDFs
├── quiz_generator.py       # Quiz generation with scoring
├── state.py                # Session state management
├── requirements.txt        # Python dependencies
├── .env.example            # Template for environment variables
├── .streamlit/
│   └── config.toml         # Streamlit theme configuration
└── README.md               # This file
```

---

## 🌐 Deployment

### Streamlit Cloud (Easiest)
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set your API keys in Streamlit Cloud's "Secrets" section
5. Deploy!

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Render / Railway
1. Add a `Procfile`:
   ```
   web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
   ```
2. Set environment variables in the platform dashboard
3. Deploy from GitHub

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- [LangChain](https://langchain.com/) — LLM orchestration framework
- [Streamlit](https://streamlit.io/) — Web UI framework
- [Google Gemini](https://ai.google.dev/) — AI model provider
- [Groq](https://groq.com/) — Fast AI inference
- [Ollama](https://ollama.com/) — Local LLM runner
