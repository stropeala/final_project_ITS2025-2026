from os import getenv

from dotenv import load_dotenv

from app.auth import hash_password
from app.extensions import PostgreSQLSession
from app.models import User

load_dotenv()

DEFAULT_USER_USERNAME = getenv("DEFAULT_USER_USERNAME")
DEFAULT_USER_PASSWORD = getenv("DEFAULT_USER_PASSWORD")

DEFAULT_ADMIN_USERNAME = getenv("DEFAULT_ADMIN_USERNAME")
DEFAULT_ADMIN_PASSWORD = getenv("DEFAULT_ADMIN_PASSWORD")


def seed_admin():
    with PostgreSQLSession() as db:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            new_admin = User(
                username=DEFAULT_ADMIN_USERNAME,
                hashed_password=hash_password(DEFAULT_ADMIN_PASSWORD),  # pyright: ignore
                role="Admin",
            )
            db.add(new_admin)
            db.commit()
            print("Successfully seeded Admin user.")


def seed_normal_user():
    with PostgreSQLSession() as db:
        user = db.query(User).filter(User.username == "user").first()
        if not user:
            new_user = User(
                username=DEFAULT_USER_USERNAME,
                hashed_password=hash_password(DEFAULT_USER_PASSWORD),  # pyright: ignore
                role="User",
            )
            db.add(new_user)
            db.commit()
            print("Successfully seeded normal user.")
