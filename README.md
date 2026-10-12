# 📚 Study Assistant — AI-Powered Learning Suite

A comprehensive AI study assistant built with **LangChain** and **Streamlit**.  
Supports **Google Gemini** (free), **Groq** (free tier), **OpenRouter**, **Ollama Cloud**, and **Ollama** (local LLM) — with automatic fallback between providers.

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
| 🧠 **Flashcard Generator** | Create flashcards from topics or PDFs, save them to decks, and review with real spaced repetition (SM-2). Export decks to CSV for Anki/Quizlet |
| ❓ **Quiz Generator** | Auto-generate MCQ quizzes with scoring and explanations; turn missed questions into flashcards in one click |
| 📈 **Progress Dashboard** | Cards due today, reviews done, day streak and recent quiz scores — saved between sessions |

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

### Option 4: OpenRouter (hundreds of models, one key)
1. Go to [openrouter.ai/keys](https://openrouter.ai/keys) and create a key
2. Paste it in the sidebar under **API Keys**
3. Pick a model — ids ending in `:free` cost nothing — or choose **✏️ Custom model...** to type any id

### Option 5: Ollama Cloud (large hosted models)
1. Sign in at [ollama.com](https://ollama.com) and create a key at [ollama.com/settings/keys](https://ollama.com/settings/keys)
2. Paste it in the sidebar under **API Keys**
3. Select **Ollama Cloud** and a model such as `gpt-oss:120b`

### 🛟 Auto-fallback
Add keys for more than one provider and keep **Auto-fallback** switched on. If the primary
provider fails (rate limit, outage, retired model), the request is retried on the next
provider that has a key, in the order Gemini → Groq → OpenRouter → Ollama Cloud.

Keys can come from the sidebar, a `.env` file (see `.env.example`), or Streamlit secrets:
`GEMINI_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `OLLAMA_API_KEY`.

---

## 📁 Project Structure

```
Study_assistant/
├── app.py                  # Main entry point with navigation and UI
├── llm_provider.py         # Centralized LLM provider (Gemini/Groq/OpenRouter/Ollama) + fallback
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

> ℹ️ Flashcard decks and quiz history are stored in a local SQLite file (`data/study.db`,
> override with `STUDY_DB_PATH`). Streamlit Cloud's disk is temporary, so progress there
> resets when the app restarts — export decks to CSV to keep them.

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
