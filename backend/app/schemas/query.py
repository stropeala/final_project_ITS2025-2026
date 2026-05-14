from pydantic import BaseModel


# Query schema for ollama response/chat generation json.
class Query(BaseModel):
    prompt: str = "Hello!"
    model: str = "gemma3:4b"
    stream: bool = False
