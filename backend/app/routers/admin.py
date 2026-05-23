from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import require_admin
from app.extensions import get_postgresql_db, get_sqlite_db
from app.models import Chat, User

# Initialize Admin router.
admin = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


# GET or POST url paths for router:


@admin.get("/users/{user_id}/chats")
def admin_list_user_chats(
    user_id: int,
    chats_db: Session = Depends(get_sqlite_db),
    users_db: Session = Depends(get_postgresql_db),
    require_admin: User = Depends(require_admin),
):
    """
    Lists every chat owned by a specific user. Admin-only.

    Checks that the user exists in PostgreSQL before returning the
    chat list.

    Args:
        user_id (int): The user whose chats to list.
        chats_db (Session): The injected SQLAlchemy session for SQLite (chats).
        users_db (Session): The injected SQLAlchemy session for PostgreSQL (users);
                            used only to validate the user_id.
        require_admin (User): Unused; injected for its side effect of enforcing
                            the Admin role requirement.

    Returns:
        list[dict]: One dict per chat with keys:
            - chat_id (str): The chat ID.
            - user_id (int): The chat's user's ID.

    Raises:
        HTTPException (404): If no user exists with the given ID.
    """
    if not users_db.query(User).filter(User.id == user_id).first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    chats = chats_db.query(Chat).filter(Chat.user_id == user_id).all()
    return [
        {
            "chat_id": chat.chat_id,
            "user_id": chat.user_id,
        }
        for chat in chats
    ]


@admin.get("/users/{user_id}/chats/{chat_id}")
def admin_get_user_chat(
    user_id: int,
    chat_id: str,
    chats_db: Session = Depends(get_sqlite_db),
    require_admin: User = Depends(require_admin),
):
    """
    Retrieves any user's chat by ID key. Admin-only.

    Args:
        user_id (int): The owning user's ID.
        chat_id (str): The chat session ID.
        chats_db (Session): The injected SQLAlchemy session for SQLite.
        require_admin (User): Unused; injected for its side effect of enforcing
                            the Admin role requirement.

    Returns:
        dict: A dictionary containing:
            - chat_id (str): The chat ID.
            - user_id (int): The chat's user's ID.
            - messages (list[dict]): The ordered list of messages.

    Raises:
        HTTPException (404): If no chat exists with that (user_id, chat_id).
    """
    chat = chats_db.get(Chat, (user_id, chat_id))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    return {
        "chat_id": chat.chat_id,
        "user_id": chat.user_id,
        "messages": chat.messages,
    }


@admin.delete("/users/{user_id}/chats/{chat_id}")
def admin_delete_chat(
    user_id: int,
    chat_id: str,
    chats_db: Session = Depends(get_sqlite_db),
    require_admin: User = Depends(require_admin),
):
    """
    Deletes any user's chat by ID key. Admin-only.

    Args:
        user_id (int): The owning user's ID.
        chat_id (str): The chat session identifier.
        chats_db (Session): The injected SQLAlchemy session for SQLite.
        require_admin (User): Unused; injected for its side effect of enforcing
                            the Admin role requirement.

    Returns:
        dict: A confirmation message.

    Raises:
        HTTPException (404): If no chat exists with that (user_id, chat_id).
    """
    chat = chats_db.get(Chat, (user_id, chat_id))
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )

    chats_db.delete(chat)
    chats_db.commit()

    return {
        "message": f"Chat {chat.chat_id} for user {user_id} deleted successfully",
    }
