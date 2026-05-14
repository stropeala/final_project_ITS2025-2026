# Personal Website with AI Chatbot

A personal website with a fully local AI chatbot — no external APIs, no data leaving your machine.

## Overview

This project is a self-hosted web app with a static personal site and an AI chat interface. The backend proxies requests to a locally running [Ollama](https://ollama.com) instance, so all inference happens on my hardware. Chat history is persisted to a local SQLite database via SQLAlchemy, so sessions survive restarts.

## Features

*   **WIP** 

## Technology

| Layer | Technology |
|---|---|
| Frontend | Vite + TypeScript (vanilla) |
| Backend | FastAPI (Python) |
| Database | SQLite via SQLAlchemy + Alembic |
| AI runtime | Ollama (local) |

## Getting Started

### 1. Install Python dependencies
 
```bash
pip install -r requirements.txt
```

### 2. Configure environment

```ini
# .env
DATABSE_URL=sqlite:///./chats.db
OLLAMA_URL=http://127.0.0.1:11434
```

### 2. Initialize Alembic
 
```bash
alembic init migrations
alembic revision --autogenerate -m "first init"
alembic upgrade head
```

### 3. Start the backend
 
```bash
uvicorn app.run:chatbot_project --reload
```

### 4. Install frontend dependencies and start the dev server
 
```bash
npm install
npm run dev
```
