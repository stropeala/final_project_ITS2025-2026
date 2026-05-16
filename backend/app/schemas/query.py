from pydantic import BaseModel


class Query(BaseModel):
    """
    Request body for Ollama generation and chat endpoints.

    Mirrors the JSON payload expected by Ollama's "/api/generate" and
    "/api/chat" endpoints. Used by the chatbot router to validate and
    forward client requests.

    Attributes:
        prompt (str): The input text to send to the model. Defaults to "Hello!".
        model (str): The Ollama model tag to use. Defaults to "gemma3:4b".
        stream (bool): Whether to stream the response. Defaults to False.
    """

    prompt: str = "Hello!"
    model: str = "gemma3:4b"
    stream: bool = False
