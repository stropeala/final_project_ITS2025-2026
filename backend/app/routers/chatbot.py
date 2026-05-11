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
def generate_text(query: Query):
    try:
        response = post(
            # sudo systemctl edit ollama
            # /etc/systemd/system/ollama.service.d/override.conf: after editing, new contents are empty, not writing file.
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
