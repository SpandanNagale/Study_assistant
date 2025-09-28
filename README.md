# Study_assistant

A generative-AI powered study assistant built using **LangChain** and Python.  
This tool helps with summarization, PDF QA, code generation, debugging, conversational agents, etc.

## Table of Contents

1. [Features](#features)  
2. [Architecture & Modules](#architecture--modules)  
3. [Setup & Installation](#setup--installation)  
4. [Usage](#usage)  
5. [Configuration & Environment Variables](#configuration--environment-variables)  
6. [Example Workflows](#example-workflows)  
7. [Limitations & Future Work](#limitations--future-work)  
8. [Contributing](#contributing)  
9. [License](#license)

---

## Features

- Summarization of text / documents  
- QA over PDF documents (upload and ask questions)  
- Conversational agents / chat interface  
- Code generation & debugging assistance  
- Memory / history tracking for chat sessions  
- Modular architecture — you can add or replace agents as needed  

## Architecture & Modules

Here are the main modules/files and their roles:

| File / Module | Purpose |
| --- | --- |
| `app.py` | Entry point / web app runner (Flask / FastAPI / whatever you use) |
| `Agents.py` | Agent orchestration / routing logic |
| `pdf_qa_bot.py` | Handles PDF-based question answering |
| `summarizer.py` | Summarization logic (text → summary) |
| `debugger_chatbot.py` | Handles debugging or code error fixing |
| `history_chatbot.py` | Manages conversational history / memory |
| `state.py` | State management / session state |
| `study_assistant.py` | Core assistant logic, glue between modules |
| `code_generator.py` | Generates code from prompts or templates |
| `requirements.txt` | Python dependencies |
| `runtime.txt` | (For deployment) runtime spec e.g. Python version |
| `.env` | Environment variables (API keys, etc.) |
| `.gitignore` | Files/folders to ignore (e.g. `.env`, `__pycache__`) |

## Setup & Installation

### Prerequisites

- Python 3.8+  
- An OpenAI API key (or any LLM provider key you plan to use)  
- (Optional) Other LLM / embedding service keys  

### Steps

1. Clone the repo  
   ```bash
   git clone https://github.com/SpandanNagale/Study_assistant.git
   cd Study_assistant
