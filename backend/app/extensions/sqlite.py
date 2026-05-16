from os import getenv

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

SQLITE_URL = getenv("SQLITE_URL", "sqlite:///./chats.db")

sqlite_engine = create_engine(
    SQLITE_URL,
    connect_args={
        "check_same_thread": False,
    },
)

SQLiteSession = sessionmaker(
    bind=sqlite_engine,
    autoflush=False,
    autocommit=False,
)


class BaseSQLite(DeclarativeBase):
    """
    Declarative base for all SQLAlchemy ORM models stored in SQLite.

    Models that inherit from this class are bound to the SQLite engine
    (currently used for chat session storage). Kept separate from
    "BasePostgreSQL" so the two databases share no metadata.
    """

    pass


def get_sqlite_db():
    """
    FastAPI dependency that yields a scoped SQLite session.

    Opens a new session per request and guarantees it is closed afterwards,
    even if the request handler raises.

    Args:
        None.

    Yields:
        Session: An open SQLAlchemy session bound to the SQLite engine.
    """
    db = SQLiteSession()

    try:
        yield db
    finally:
        db.close()
