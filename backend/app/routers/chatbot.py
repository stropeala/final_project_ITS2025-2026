from fastapi import APIRouter, HTTPException
from requests import RequestException, post

from ..models import Query

# Initialize ChatBOT router
chatbot = APIRouter(tags=["ChatBOT"])


# GET or POST url paths for router
@chatbot.get("/")
def index():
    """PLACEHOLDER index page"""
    return {
        "message": "no AI for you yet!",
    }


@chatbot.post("/generate")
def generate_text(query: Query):
    """
    Generates text using Ollama.

    Args:
        query: An object containing the model name, prompt, and stream options.

    Returns:
        A dictionary containing the generated text.

    Raises:
        HTTPException: If there's an error communicating with Ollama.
    """
    try:
        response = post(
            url="http://127.0.0.1:11434/api/generate",
            json={
                "model": query.model,
                "prompt": query.prompt,
                "stream": query.stream,
            },
        )

        response.raise_for_status()

        return {"generated_text": response.json()["response"]}

    except RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with Ollama: {str(error)}",
        )
