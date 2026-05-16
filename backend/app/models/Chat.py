from typing import Dict, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.extensions import BaseSQLite


class Chat(BaseSQLite):
    """
    SQLAlchemy ORM model for a chatbot conversation, stored in SQLite.

    Backs the "Chats" table. Each row holds the full message history for
    a single session, persisted as a JSON list of role/content pairs.

    Attributes:
        id (str): The client-supplied session identifier. Primary key,
            indexed. Must be unique across all chats.
        messages (List[Dict[str, str]]): The ordered conversation history.
            Each entry is a dict like {"role": "user" | "assistant",
            "content": "..."}. Non-nullable; defaults to an empty list.
    """

    __tablename__ = "Chats"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
    )
    messages: Mapped[List[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
