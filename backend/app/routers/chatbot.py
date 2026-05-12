from fastapi import APIRouter, HTTPException
from requests import RequestException, get, post

from app.schemas import Chat, Query, chats

# Initialize ChatBOT router.
chatbot = APIRouter(tags=["ChatBOT"])


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
async def generate_text(query: Query):
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
            url="http://127.0.0.1:11434/api/generate",  # "Generate a response" endpoint.
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
async def list_models():
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
            url="http://localhost:11434/api/tags"  # "List models" endpoint.
        )

        response.raise_for_status()

        return {"models": response.json()["models"]}

    except RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching models from Ollama: {str(error)}",
        )


@chatbot.post("/chat/start")
async def start_chat(chat_id: str):
    """
    Creates an empty "Chat" entry  keyed by a "chat_id".

    Args:
        chat_id (str): A unique id for the session.
                    Must not already exist.

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException (400): If a chat with the given "chat_id" already exists.
    """

    if chat_id in chats:
        raise HTTPException(
            status_code=400,
            detail="Chat ID already exists",
        )

    chats[chat_id] = Chat(id=chat_id)

    return {"message": f"Chat {chat_id} started"}


@chatbot.post("/chat/{chat_id}/message")
async def add_message(chat_id: str, query: Query):
    """
    Appends "query.prompt" to the conversation history as a "user" turn,
    sends the full message history to the Ollama "/api/chat" endpoint, then
    appends the assistant's reply to history before returning it. Conversation
    context is preserved for the same "chat_id".

    Args:
        chat_id (str): A unique id for the session (created via "/chat/start").
        query (Query): The generation request, containing:
            - prompt (str): The input text to send to the model.
            - model (str): The Ollama model to use.
            - stream (bool): Whether to stream the response.

    Returns:
        dict: A dictionary with a single key:
            - generated_text (str): The assistant's reply for this turn.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
        HTTPException (500): If the request to Ollama fails for any reason.
    """
    if chat_id not in chats:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    chat = chats[chat_id]

    chat.messages.append(
        {
            "role": "user",
            "content": query.prompt,
        },
    )

    try:
        response = post(
            url="http://127.0.0.1:11434/api/chat",  # "Generate a chat message" endpoint.
            json={
                "model": query.model,
                "messages": chat.messages,  # pyright: ignore
                "stream": query.stream,
            },
        )

        response.raise_for_status()
        generated_text = response.json()["message"]["content"]

        chat.messages.append(
            {
                "role": "assistant",
                "content": generated_text,
            },
        )

        return {"generated_text": generated_text}

    except RequestException as error:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with Ollama: {str(error)}",
        )


@chatbot.get("/chat/{chat_id}")
async def get_chat(chat_id: str):
    """
    Retrieve a full existing chat session.

    Args:
        chat_id (str): A unique id for the session (created via "/chat/start").

    Returns:
        Chat: The chat object, containing:
            - id (str): The session identifier.
            - messages (list[dict]): The ordered list of messages.

    Raises:
        HTTPException (404): If no chat session exists for the given "chat_id".
    """

    if chat_id not in chats:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    return chats[chat_id]
