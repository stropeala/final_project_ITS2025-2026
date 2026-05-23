from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, verify_password
from app.extensions import get_postgresql_db
from app.models import User
from app.schemas import LoginRequest, TokenOut, UserOut

auth = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@auth.post("/login", response_model=TokenOut)
def login(
    payload: LoginRequest,
    user_db: Session = Depends(get_postgresql_db),
):
    """
    Authenticates a user with username and password and issue a JWT.

    Looks up the user by username then verifies the password against the stored
    bcrypt hash and returns a signed access token on success.

    Args:
        payload (LoginRequest): The login credentials, containing:
            - username (str): The user's username.
            - password (str): The user's password.
        user_db (Session): The injected SQLAlchemy session for PostgreSQL.

    Returns:
        TokenOut: A bearer token wrapper containing:
            - access_token (str): The signed JWT.
            - token_type (str): Always "bearer".

    Raises:
        HTTPException (401): If the username doesn't exist or the password
                            doesn't match.
    """
    user = user_db.query(User).filter(User.username == payload.username).first()

    # We combine both checks so we don't reveal WHICH one failed
    # (otherwise an attacker could probe which usernames exist).
    if not user or not verify_password(payload.password, user.hashed_password):  # pyright: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token(
        {
            "sub": str(user.id),
            "role": user.role,
        },
    )
    return TokenOut(access_token=token)


@auth.get("/profile", response_model=UserOut)
def profile(
    current_user: User = Depends(get_current_user),
):
    """
    Returns the currently authenticated user.

    Args:
        current_user (User): The user resolved from the bearer token
                            by the get_current_user dependency.

    Returns:
        UserOut: The current user's public fields (id, username, role).
    """
    return current_user
