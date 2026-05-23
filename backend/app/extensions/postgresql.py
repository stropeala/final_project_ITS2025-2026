from os import getenv

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

POSTGRESQL_URL = getenv("POSTGRESQL_URL")
if not POSTGRESQL_URL:
    raise RuntimeError(
        "POSTGRESQL_URL environment variable is not set. Check your .env file."
    )

postgresql_engine = create_engine(POSTGRESQL_URL)

PostgreSQLSession = sessionmaker(
    bind=postgresql_engine,
    autoflush=False,
    autocommit=False,
)


class BasePostgreSQL(DeclarativeBase):
    """
    Declarative base for all SQLAlchemy ORM models stored in PostgreSQL.

    Models that inherit from this class are bound to the PostgreSQL engine
    (currently used for user accounts). Kept separate from "BaseSQLite"
    so the two databases share no metadata.
    """

    pass


def get_postgresql_db():
    """
    FastAPI dependency that yields a PostgreSQL session.

    Opens a new session per request and guarantees it is closed afterwards,
    even if the request handler raises.

    Args:
        None.

    Yields:
        Session: An open SQLAlchemy session bound to the PostgreSQL engine.
    """
    db = PostgreSQLSession()

    try:
        yield db
    finally:
        db.close()
