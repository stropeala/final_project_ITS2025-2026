from typing import Dict, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.extensions import Base


class Chat(Base):
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
