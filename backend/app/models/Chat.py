from typing import Dict, List

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.extensions import BaseSQLite


class Chat(BaseSQLite):
    """
    SQLAlchemy ORM model for a chatbot chat, stored in SQLite.

    Backs the "Chats" table. Each row holds the full message history for
    a single session, persisted as a JSON list of role and content pairs.

    Attributes:
        user_id (int): The user identifier from the Users db. Primary key,
                    indexed.
        chat_id (str): The user-supplied session identifier. Primary key,
                    indexed. Must be unique across all chats.
        messages (List[Dict[str, str]]): The ordered conversation history.
                    Each entry is a dict like {"role": "user" or "assistant",
                    "content": "..."}. Non-nullable; defaults to an empty list.
    """

    __tablename__ = "Chats"

    user_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )
    chat_id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        index=True,
    )
    messages: Mapped[List[Dict[str, str]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )
