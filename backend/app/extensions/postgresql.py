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
    pass


def get_postgresql_db():
    """
    FastAPI dependency that yields a scoped PostgreSQL session.

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
