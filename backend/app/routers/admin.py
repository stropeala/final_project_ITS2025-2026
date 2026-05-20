from fastapi import APIRouter, Depends, HTTPException
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
    if not users_db.query(User).filter(User.id == user_id).first():
        raise HTTPException(
            status_code=404,
            detail="User not found.",
        )

    chats = chats_db.query(Chat).filter(Chat.user_id == user_id).all()
    return [
        {
            "id": chat.id,
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
    chat = chats_db.get(Chat, (user_id, chat_id))
    if not chat:
        raise HTTPException(
            status_code=404,
            detail="Chat not found",
        )

    return {
        "id": chat.id,
        "user_id": chat.user_id,
        "messages": chat.messages,
    }
