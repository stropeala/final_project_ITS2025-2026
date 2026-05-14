from os import getenv

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from requests import RequestException, get, post
from sqlalchemy.orm import Session

from app.extensions import get_sqlite_db
from app.models import Chat
from app.schemas import Query

load_dotenv()

OLLAMA_URL = getenv("OLLAMA_URL", "http://localhost:11434")

# Initialize ChatBOT router.
chatbot = APIRouter(
    prefix="/chat",
    tags=["ChatBOT"],
)


# GET or POST url paths for router.
@chatbot.get("/")
async def index():
    """
    Checker for the ChatBOT router.

    Args:
        None.

    Returns:
        dict: A placeholder message.
    """
    return {
        "message": "no AI for you yet!",
    }


@chatbot.post("/generate")
def generate_text(query: Query):
    """
    Generate a single-turn text response from a given prompt via Ollama.
    Sends the prompt to the Ollama "/api/generate" endpoint and returns
    the model's raw text output.

    Args:
        query (Query): The generation request, containing:
            - prompt (str): The input text to send to the model.
            - model (str): The Ollama model to use.
            - stream (bool): Whether to stream the response.

    Returns:
        dict: A dictionary with a single key:
            - generated_text (str): The model's response to the prompt.

    Raises:
        HTTPException (500): If the request to Ollama fails for any reason.
    """
    try:
        response = post(
            url=OLLAMA_URL + "/api/generate",  # "Generate a response" endpoint.
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


@chatbot.get("/models")
def list_models():
    """
    Queries the Ollama "/api/tags" endpoint and returns the full list of models.

    Args:
        None.

    Returns:
        dict: A dictionary with a single key:
            - models (list[dict]): A list of model objects.

    Raises:
        HTTPException (500): If the request to Ollama fails for any reason.
    """
    try:
        response = get(
            url=OLLAMA_URL + "/api/tags"  # "List models" endpoint.
        )

        response.raise_for_status()
        return {"models": response.json()["models"]}

    except RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models from Ollama: {str(error)}",
        )


@chatbot.post("/start/{chat_id}")
def start_chat(chat_id: str, db: Session = Depends(get_sqlite_db)):
    """
    Creates an empty "Chat" entry keyed by a "chat_id".

    Args:
        chat_id (str): A unique id for the session, passed as a path parameter.
                    Must not already exist.
        db (Session): The injected SQLAlchemy database session.

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException (400): If a chat with the given "chat_id" already exists.
    """
    if db.get(Chat, chat_id):
        raise HTTPException(
            status_code=400,
            detail="Chat ID already exists",
        )

    db.add(Chat(id=chat_id, messages=[]))
    db.commit()

    return {"message": f"Chat {chat_id} started"}


@chatbot.post("/{chat_id}/message")
def add_message(chat_id: str, query: Query, db: Session = Depends(get_sqlite_db)):
    """
    Appends "query.prompt" to the DB conversation history as a "user" turn,
    sends the full message history to Ollama "/api/chat", then appends
    the assistant's reply before returning it.

    Args:
        chat_id (str): A unique id for the session (created via "/chat/start").
        query (Query): The generation request, containing:
            - prompt (str): The input text to send to the model.
            - model (str): The Ollama model to use.
            - stream (bool): Whether to stream the response.
        db (Session): The injected SQLAlchemy database session.

    Returns:
        dict: A dictionary with a single key:
            - generated_text (str): The assistant's reply for this turn.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
        HTTPException (500): If the request to Ollama fails for any reason.
    """
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    updated_messages = list(chat.messages) + [
        {
            "role": "user",
            "content": query.prompt,
        },
    ]
    chat.messages = updated_messages
    db.flush()

    try:
        response = post(
            url=OLLAMA_URL + "/api/chat",  # "Generate a chat message" endpoint.
            json={
                "model": query.model,  # pyright: ignore
                "messages": chat.messages,
                "stream": query.stream,
            },
        )

        response.raise_for_status()
        generated_text = response.json()["message"]["content"]

        chat.messages = list(chat.messages) + [
            {
                "role": "assistant",
                "content": generated_text,
            }
        ]
        db.commit()

        return {"generated_text": generated_text}

    except RequestException as error:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with Ollama: {str(error)}",
        )


@chatbot.get("/{chat_id}")
def get_chat(chat_id: str, db: Session = Depends(get_sqlite_db)):
    """
    Retrieve a full existing chat session from the DB.

    Args:
        chat_id (str): A unique id for the session (created via "/chat/start").
        db (Session): The injected SQLAlchemy database session.

    Returns:
        dict: A dictionary containing:
            - id (str): The session identifier.
            - messages (list[dict]): The ordered list of messages.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
    """
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    return {"id": chat.id, "messages": chat.messages}


@chatbot.delete("/{chat_id}")
def delete_chat(chat_id: str, db: Session = Depends(get_sqlite_db)):
    """
    Deletes an existing chat session from the DB.

    Args:
        chat_id (str): A unique id for the session (created via "/chat/start").
        db (Session): The injected SQLAlchemy database session.

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
    """
    chat = db.get(Chat, chat_id)
    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    db.delete(chat)
    db.commit()

    return {"message": f"Chat {chat.id} deleted successfully"}
