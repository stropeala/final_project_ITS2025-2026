# Personal Website with AI Chatbot

Website powered by a fully localized AI chatbot with no API integration and no data leaving your machine.

## Overview

This project is a local web application with a website and AI chatbot interface. All requests are proxied through the backend to a locally hosted [Ollama](https://ollama.com) service, which means that the AI will run locally on my machine. Any chat conversation data is also stored locally using a SQLite database via SQLAlchemy.

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
SQLITE_URL=sqlite:///./chats.db
POSTGRESQL_URL=postgresql://user:password@localhost/users
OLLAMA_URL=http://127.0.0.1:11434

SECRET_KEY=ad8f9c8490c04b018490c00c0d8f9d8f904b018490c00c0d8f9d
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

DEFAULT_USER_USERNAME="user"
DEFAULT_USER_PASSWORD="user123"
DEFAULT_ADMIN_USERNAME="admin"
DEFAULT_ADMIN_PASSWORD="admin123"
```

### 2. Initialize Alembic
 
```bash
alembic init --template multidb migrations
```

### 3. Add DB engine urls in alembic.ini
```ini
databases = engine1, engine2

[engine1]
sqlalchemy.url = sqlite:///./chats.db

[engine2]
sqlalchemy.url = postgresql://user:password@localhost/users
```

### 4. Modify env.py inside migrations
```python
from app.extensions import BasePostgreSQL, BaseSQLite
from app.models import Chat, User
```
#### &
```python
target_metadata = {
    "engine1": BaseSQLite.metadata,
    "engine2": BasePostgreSQL.metadata,
}
```

### 5. Finish setting up alembic 
```bash
alembic revision --autogenerate -m "first init"
alembic upgrade head
```

### 6. Start the backend
 
```bash
uvicorn app.run:chatbot_project --reload
```

### 7. Install frontend dependencies and start the dev server
 
```bash
npm install
npm run dev
```

## 8. ENJOY!
