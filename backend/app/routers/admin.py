from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import hash_password, require_admin
from app.extensions import get_postgresql_db, get_sqlite_db
from app.models import Chat, User
from app.schemas import UserCreate, UserOut

# Initialize Admin router.
admin = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


# GET or POST url paths for router:


@admin.post("/users", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    users_db: Session = Depends(get_postgresql_db),
    require_admin: User = Depends(require_admin),
):
    """
    Creates a new user. Admin-only.

    Hashes the supplied password before persisting. Usernames must be unique.

    Args:
        payload (UserCreate): The new user fields, containing:
            - username (str): The desired username; must be unique.
            - password (str): The plaintext password (will be hashed).
            - role (Literal["Admin", "User"]): The role to assign. Defaults to "User".
        users_db (Session): The injected SQLAlchemy session for PostgreSQL.
        require_admin (User): Unused; injected for its side effect of enforcing
                            the Admin role requirement.

    Returns:
        UserOut: The newly created user's public fields.

    Raises:
        HTTPException (400): If the username is already taken.
    """
    existing = users_db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="That username is already taken.",
        )

    new_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )

    users_db.add(new_user)
    users_db.commit()
    users_db.refresh(new_user)

    return new_user


@admin.get("/users", response_model=list[UserOut])
def list_users(
    users_db: Session = Depends(get_postgresql_db),
    require_admin: User = Depends(require_admin),
):
    """
    Lists every registered user. Admin-only.

    Args:
        users_db (Session): The injected SQLAlchemy session for PostgreSQL.
        require_admin (User): Unused; injected for its side effect of enforcing
                            the Admin role requirement.

    Returns:
        list[UserOut]: All user records, serialized to their public fields.
    """
    return users_db.query(User).all()


@admin.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    users_db: Session = Depends(get_postgresql_db),
    require_admin: User = Depends(require_admin),
):
    """
    Deletes a user by ID. Admin-only.

    Admins are prevented from deleting their own account to avoid locking
    the system out.

    Args:
        user_id (int): The ID of the user to delete.
        users_db (Session): The injected SQLAlchemy session for PostgreSQL.
        require_admin (User): The authenticated admin making the request.

    Returns:
        None: 204 No Content on success.

    Raises:
        HTTPException (400): If the admin tries to delete their own account.
        HTTPException (404): If no user exists with the given ID.
    """
    # Prevent an admin from accidentally deleting their own account.
    if user_id == require_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account.",
        )

    user = users_db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    users_db.delete(user)
    users_db.commit()


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
