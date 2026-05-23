from os import getenv

from dotenv import load_dotenv

from app.auth import hash_password
from app.extensions import PostgreSQLSession
from app.models import User

load_dotenv()

DEFAULT_USER_USERNAME = getenv("DEFAULT_USER_USERNAME")
DEFAULT_USER_PASSWORD = getenv("DEFAULT_USER_PASSWORD")
if not DEFAULT_USER_USERNAME or not DEFAULT_USER_PASSWORD:
    raise RuntimeError(
        "DEFAULT_USER_USERNAME or DEFAULT_USER_PASSWORD environment variable is not set. Check your .env file."
    )

DEFAULT_ADMIN_USERNAME = getenv("DEFAULT_ADMIN_USERNAME")
DEFAULT_ADMIN_PASSWORD = getenv("DEFAULT_ADMIN_PASSWORD")
if not DEFAULT_ADMIN_USERNAME or not DEFAULT_ADMIN_PASSWORD:
    raise RuntimeError(
        "DEFAULT_ADMIN_USERNAME or DEFAULT_ADMIN_PASSWORD environment variable is not set. Check your .env file."
    )


def seed_admin():
    """
    Ensures a default Admin account exists in PostgreSQL.

    Looks up an existing user whose username matches DEFAULT_ADMIN_USERNAME.
    If none is found it then creates a new Admin row with the hashed
    DEFAULT_ADMIN_PASSWORD. Runs once on application startup via the FastAPI lifespan.

    Args:
        None.

    Returns:
        None.
    """
    with PostgreSQLSession() as user_db:
        admin = (
            user_db.query(User).filter(User.username == DEFAULT_ADMIN_USERNAME).first()
        )
        if not admin:
            new_admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),  # pyright: ignore
                role="Admin",
            )
            user_db.add(new_admin)
            user_db.commit()
            print("Successfully seeded Admin user.")


def seed_normal_user():
    """
    Ensures a default normal user account exists in PostgreSQL.

    Looks up an existing user whose username matches DEFAULT_USER_USERNAME.
    If none is found it then creates a new normal user row with the hashed
    DEFAULT_USER_PASSWORD. Runs once on application startup via the FastAPI lifespan.

    Args:
        None.

    Returns:
        None.
    """
    with PostgreSQLSession() as user_db:
        user = (
            user_db.query(User).filter(User.username == DEFAULT_USER_USERNAME).first()
        )
        if not user:
            new_user = User(
                username=DEFAULT_USER_USERNAME,
                hashed_password=hash_password(DEFAULT_USER_PASSWORD),  # pyright: ignore
                role="User",
            )
            user_db.add(new_user)
            user_db.commit()
            print("Successfully seeded normal user.")
