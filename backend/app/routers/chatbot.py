from os import getenv

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, status
from requests import RequestException, get, post
from sqlalchemy.orm import Session

from app.auth import get_current_user, role_user
from app.extensions import get_sqlite_db
from app.models import Chat, User
from app.schemas import Query

load_dotenv()

OLLAMA_URL = getenv("OLLAMA_URL", "http://localhost:11434")

# Initialize ChatBOT router.
chatbot = APIRouter(
    prefix="/chat",
    tags=["ChatBOT"],
)


# GET or POST url paths for router:


@chatbot.post("/generate")
def generate_one_response(
    query: Query,
    require_user: User = Depends(role_user),
):
    """
    Generates a single-turn text response from a given prompt via Ollama.
    Sends the prompt to the Ollama "/api/generate" endpoint and returns
    the model's text output.

    Args:
        query (Query): The generation request, containing:
            - prompt (str): The input text to send to the model.
            - model (str): The Ollama model to use.
            - stream (bool): Whether to stream the response.
        require_user (User): Unused; injected for its side effect of enforcing
                            the User role requirement.

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
            timeout=(5, 120),
        )

        response.raise_for_status()
        return {"generated_text": response.json()["response"]}

    except RequestException as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Ollama: {str(error)}",
        )


@chatbot.get("/models")
def list_models(
    require_user: User = Depends(role_user),
):
    """
    Queries the Ollama "/api/tags" endpoint and returns the full list of models.

    Args:
        require_user (User): Unused; injected for its side effect of enforcing
                            the User role requirement.

    Returns:
        dict: A dictionary with a single key:
            - models (list[dict]): A list of model objects.

    Raises:
        HTTPException (500): If the request to Ollama fails for any reason.
    """
    try:
        response = get(
            url=OLLAMA_URL + "/api/tags",  # "List models" endpoint.
            timeout=(5, 10),
        )

        response.raise_for_status()
        return {
            "models": response.json()["models"],
        }

    except RequestException as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching models from Ollama: {str(error)}",
        )


@chatbot.post("/{chat_id}")
def new_chat(
    chat_id: str,
    chats_db: Session = Depends(get_sqlite_db),
    current_user: User = Depends(get_current_user),
):
    """
    Creates an empty "Chat" entry keyed by a "chat_id".

    Args:
        chat_id (str): A unique id for the session, passed as a path parameter.
                    Must not already exist.
        chats_db (Session): The injected SQLAlchemy database session.
        current_user (User): The authenticated user, it provides the
                            user_id key.

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException (400): If a chat with the given "chat_id" already exists.
    """
    if chats_db.get(Chat, (current_user.id, chat_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Chat ID already exists",
        )

    chats_db.add(
        Chat(
            user_id=current_user.id,
            chat_id=chat_id,
            messages=[],
        ),
    )
    chats_db.commit()

    return {"message": f"Chat {chat_id} started"}


@chatbot.post("/{chat_id}/message")
def add_chat_message(
    chat_id: str,
    query: Query,
    chats_db: Session = Depends(get_sqlite_db),
    current_user: User = Depends(get_current_user),
):
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
        chats_db (Session): The injected SQLAlchemy database session.
        current_user (User): The authenticated user, it provides the
                            user_id key.

    Returns:
        dict: A dictionary with a single key:
            - generated_text (str): The assistant's reply for this turn.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
        HTTPException (500): If the request to Ollama fails for any reason.
    """
    chat = chats_db.get(Chat, (current_user.id, chat_id))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    updated_messages = list(chat.messages) + [
        {
            "role": "user",
            "content": query.prompt,
        },
    ]
    chat.messages = updated_messages
    chats_db.flush()

    try:
        response = post(
            url=OLLAMA_URL + "/api/chat",  # "Generate a chat message" endpoint.
            json={
                "model": query.model,  # pyright: ignore
                "messages": chat.messages,
                "stream": query.stream,
            },
            timeout=(5, 120),
        )

        response.raise_for_status()
        generated_text = response.json()["message"]["content"]

        chat.messages = list(chat.messages) + [
            {
                "role": "assistant",
                "content": generated_text,
            }
        ]
        chats_db.commit()

        return {"generated_text": generated_text}

    except RequestException as error:
        chats_db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with Ollama: {str(error)}",
        )


@chatbot.get("/chats")
def get_chats(
    chats_db: Session = Depends(get_sqlite_db),
    current_user: User = Depends(get_current_user),
):
    """
    Lists every chat owned by the current user.

    Args:
        chats_db (Session): The injected SQLAlchemy database session.
        current_user (User): The authenticated user, it provides the
                            user_id key.

    Returns:
        list[dict]: One dict per chat with keys:
            - chat_id (str): The chat ID.
    """
    chats = chats_db.query(Chat).filter(Chat.user_id == current_user.id).all()

    return [{"chat_id": chat.chat_id} for chat in chats]


@chatbot.get("/{chat_id}")
def get_chat(
    chat_id: str,
    chats_db: Session = Depends(get_sqlite_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves a full existing chat session from the DB.

    Args:
        chat_id (str): A unique id for the session (created via "/chat/start").
        chats_db (Session): The injected SQLAlchemy database session.
        current_user (User): The authenticated user, it provides the
                            user_id key.

    Returns:
        dict: A dictionary containing:
            - chat_id (str): The session identifier.
            - messages (list[dict]): The ordered list of messages.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
    """
    chat = chats_db.get(Chat, (current_user.id, chat_id))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return {"chat_id": chat.chat_id, "messages": chat.messages}


@chatbot.delete("/{chat_id}")
def delete_chat(
    chat_id: str,
    chats_db: Session = Depends(get_sqlite_db),
    current_user: User = Depends(get_current_user),
):
    """
    Deletes an existing chat session from the DB.

    Args:
        chat_id (str): A unique id for the session (created via "/chat/start").
        chats_db (Session): The injected SQLAlchemy database session.
        current_user (User): The authenticated user, it provides the
                    user_id key to be along the chat_id key.

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
    """
    chat = chats_db.get(Chat, (current_user.id, chat_id))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    chats_db.delete(chat)
    chats_db.commit()

    return {"message": f"Chat {chat.chat_id} deleted successfully"}
