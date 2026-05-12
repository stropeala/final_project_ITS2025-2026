from typing import Dict, List

from pydantic import BaseModel


# Query schema for ollama response generation json.
class Query(BaseModel):
    prompt: str
    model: str = "gemma3:4b"
    stream: bool = False


# Chat schema for ollama chat generation json.
class Chat(BaseModel):
    id: str
    messages: List[Dict[str, str]] = []


# Empty chats dictionary.
chats: Dict[str, Chat] = {}
