from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import BasePostgreSQL


class User(BasePostgreSQL):
    """
    SQLAlchemy ORM model for a registered account, stored in PostgreSQL.

    Backs the "Users" table. Each row represents a single account that can
    authenticate against "/auth/login" and act under the privileges of its
    assigned role.

    Attributes:
        id (int): Auto-incrementing primary key. Indexed.
        username (str): Unique login name. Indexed, non-nullable.
        hashed_password (str): The bcrypt hash of the user's password.
            Non-nullable.
        role (str): The user's role, either "Admin" or "User". Defaults
            to "User". Enforced at the application layer via "require_role".
    """

    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    username: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String,
        nullable=False,
        default="User",
    )
