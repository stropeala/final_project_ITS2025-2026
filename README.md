# Personal Website with Local AI Chatbot

A personal portfolio website with a built-in, **fully local** AI chatbot — no third-party API, no data leaving your machine.

> **Status: work in progress.** The core stack (auth, chat, admin, migrations) is functional. More features are WIP.

---

## Overview

The frontend is a generated mock-up portfolio site with a private chatbot behind a login. Access is invite-only and there is no public sign-up. The owner creates accounts for family, friends, and colleagues from an admin panel, and only those accounts can use the chatbot.

Everything runs locally. The browser talks to a FastAPI backend, which:

- authenticates users and enforces role-based access (`Admin` / `User`)
- stores user accounts in **[AWS](https://aws.amazon.com/rds/postgresql/)-PostgreSQL** and chat histories in **Local-SQLite** (both via SQLAlchemy with Alembic managing the schema & migrations)
- sends prompts to a local **[Ollama](https://ollama.com)** runtime so no conversation data is ever sent to an external service.

---

## Technology

| Layer       | Technology                                              |
| ----------- | ------------------------------------------------------- |
| Frontend    | Vite + TypeScript (vanilla, no framework)               |
| Backend     | FastAPI (Python)                                        |
| Auth        | JWT (python-jose) + bcrypt (passlib)                    |
| Databases   | SQLite (chats) & PostgreSQL (users), via SQLAlchemy     |
| Migrations  | Alembic (multi-database setup)                          |
| AI runtime  | Ollama (local)                                          |

---

## Architecture

The frontend never communicates with the databases or Ollama directly — everything is mediated by the backend. In development, the Vite dev server proxies the `/auth`, `/chat`, and `/admin` path prefixes to the backend on port `8000`, so the browser stays same-origin and the frontend calls the exact same URLs the API defines.

### What happens when you send a message

A single chat turn touches every layer.

```mermaid
flowchart TD
    A["User sends a message:<br/>chat_id/message + JWT"]
    B["Backend verifies token<br/>then loads user from PostgreSQL"]
    C["Save user turn to SQLite<br/>then appends to chat history"]
    D["Forward history to Ollama<br/>and the local model generates a reply"]
    E["Save reply to SQLite,<br/>on generation error it rolls back"]
    F["Return reply to frontend<br/>then renders reply"]

    A --> B --> C --> D --> E --> F
```

The user's message is saved *before* calling Ollama and if the model call fails, that turn is rolled back so a failed request doesn't leave a useless message in the history.


---

## Project structure

```
backend/
├── app/
│   ├── auth/                 
│   │   ├── auth_handler.py   # hash/verify, JWT handling, , get_current_user, role guards
│   │   └── seed_users.py     # seeds default admin + user on startup
│   ├── extensions/           
│   │   ├── postgresql.py     # PostgreSQL engine, BasePostgreSQL, get_postgresql_db
│   │   └── sqlite.py         # SQLite engine, BaseSQLite, get_sqlite_db
│   ├── models/               
│   │   ├── User.py           # Users table (PostgreSQL)
│   │   └── Chat.py           # Chats table (SQLite)
│   ├── routers/              
│   │   ├── home.py           
│   │   ├── auth_router.py    # /auth/login, /auth/profile
│   │   ├── chatbot.py        # /chat/* — models, generate, create, message, list, get, delete
│   │   └── admin.py          # /admin/* — user + chat moderation (Admin only)
│   ├── schemas/              
│   │   ├── auth_schema.py    # LoginRequest, UserCreate, TokenOut, UserOut
│   │   └── query.py          # Query (prompt, model, stream)
│   └── run.py                # FastAPI app
├── migrations/               # Alembic (multidb) + env.py
├── alembic.ini
└── example.env               # copy to .env and fill in
```

---

## Getting Started

> **Prerequisites:** Ollama] installed with at least one model pulled, a reachable PostgreSQL database

### 1. Install Python dependencies
 
```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

```ini
# .env example

# DBs & Ollama urls
SQLITE_URL=sqlite:///./chats.db
POSTGRESQL_URL=postgresql://user:password@localhost/users
OLLAMA_URL=http://127.0.0.1:11434

# Auth enviroment variables
SECRET_KEY=super-secret-key-69-420
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Seeded users
DEFAULT_USER_USERNAME="user"
DEFAULT_USER_PASSWORD="user123"
DEFAULT_ADMIN_USERNAME="admin"
DEFAULT_ADMIN_PASSWORD="admin123"
```

- **Generate a real `SECRET_KEY`.** It signs your JWTs
- **The `users` database must already exist** on your PostgreSQL server.

### 3. Set up the database schema via Alembic

This project uses Alembic's **multidb** template, since it manages two databases at once (SQLite for chats, PostgreSQL for users). 
I already have a `migrations/` directory in the repo because my PSQL db already exists and i need it's versions. 

You shold delete my `migrations/` and begin anew with your own PSQL server:

```bash
alembic init --template multidb migrations
```

Then edit `migrations/env.py`:

Add to the imports:

```python
from app.extensions import (
    POSTGRESQL_URL,
    SQLITE_URL,
    BasePostgreSQL,
    BaseSQLite,
)
from app.models import Chat, User
```

Below `config = context.config`, point each engine at the same URLs the app uses:

```python
config.set_section_option("engine1", "sqlalchemy.url", SQLITE_URL)
config.set_section_option("engine2", "sqlalchemy.url", POSTGRESQL_URL)
```

And set the metadata so autogenerate knows which models belong to which database:

```python
target_metadata = {
    "engine1": BaseSQLite.metadata,
    "engine2": BasePostgreSQL.metadata,
}
```

Generate and apply the first migration:

```bash
alembic revision --autogenerate -m "first init"
alembic upgrade head
```

- **After changing a model:** `alembic revision --autogenerate -m "..."`, then `alembic upgrade head`.

### 4. Start the backend

```bash
uvicorn app.run:chatbot_project --reload
```

On startup the app seeds the default admin and user accounts if they don't already exist.

### 5. Start the frontend

```bash
cd ../frontend
npm install
npm run dev
```

Open it and use **Private chat** to log in.

## 6. ENJOY!
