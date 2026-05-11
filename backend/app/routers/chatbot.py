from fastapi import APIRouter, HTTPException
from requests import RequestException, post

from ..models import Query

chatbot = APIRouter(tags=["ChatBOT"])


@chatbot.get("/")
def index():
    return {
        "message": "no AI for you yet!",
    }


@chatbot.post("/generate")
async def generate_text(query: Query):
    try:
        response = post(
            url="http://localhost:11434/api/generate",
            json={
                "model": query.model,
                "prompt": query.prompt,
            },
        )

        response.raise_for_status()

        return {"generated_text": response.json()["response"]}

    except RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with Ollama: {str(error)}",
        )
