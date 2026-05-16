# Personal Website with AI Chatbot

Website powered by a fully localized AI chatbot with no API integration and no data leaving your machine.

## Overview

This project is a local web application with a website and AI chatbot interface. All requests are proxied through the backend to a locally hosted [Ollama](https://ollama.com) service, which means that the AI will run locally on my machine. Any chat conversation data is stored locally using an SQLite database via SQLAlchemy and users are stored using PostgreSQL also via SQLAlchemy.

## Features
*   **WIP** 
*   **THIS IS AN UNFINISHED PROJECT** 
*   **WIP** 

## Technology

| Layer | Technology |
|---|---|
| Frontend | Vite + TypeScript (vanilla) |
| Backend | FastAPI (Python) |
| Database | SQLite & PostgreSQL via SQLAlchemy + Alembic |
| AI runtime | Ollama (local) |

## Getting Started

### This assumes you have Ollama installed and a PosgreSQL db setup already

### 1. Install Python dependencies
 
```bash
pip install -r requirements.txt
```

### 2. Configure environment

```ini
# .env example
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

### 3. Modify env.py inside migrations dir

#### Add this in the imports

```python
from app.extensions import (
    POSTGRESQL_URL,
    SQLITE_URL,
    BasePostgreSQL,
    BaseSQLite,
)
from app.models import Chat, User
```

#### then add this below ```config = context.config```

```python
# Override the engine sqlalchemy.url values from alembic.ini with the
# same URLs the running FastAPI app uses. This keeps the migrations and
# application pointed at the same databases. The variables are now in
# .env instead of alembic.ini
config.set_section_option("engine1", "sqlalchemy.url", SQLITE_URL)
config.set_section_option("engine2", "sqlalchemy.url", POSTGRESQL_URL)
```

#### and finally modify ```target_metadata = {}```

```python
target_metadata = {
    "engine1": BaseSQLite.metadata,
    "engine2": BasePostgreSQL.metadata,
}
```

### 4. Finish setting up alembic 

```bash
alembic revision --autogenerate -m "first init"
alembic upgrade head
```

### 5. Start the backend
 
```bash
uvicorn app.run:chatbot_project --reload
```

### 6. Install frontend dependencies and start the dev server
 
```bash
npm install
npm run dev
```

## 7. ENJOY!
