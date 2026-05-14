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
    pass


def get_sqlite_db():
    """
    FastAPI dependency that yields a scoped PostgreSQL session.

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
