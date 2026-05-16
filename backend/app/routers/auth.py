from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    require_admin,
    verify_password,
)
from app.extensions import get_postgresql_db
from app.models import User
from app.schemas import LoginRequest, TokenOut, UserCreate, UserOut

auth = APIRouter(prefix="/auth", tags=["Auth"])


@auth.post("/login", response_model=TokenOut)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_postgresql_db),
):
    """
    Authenticate a user with username/password and issue a JWT.

    Looks up the user by username, verifies the password against the stored
    bcrypt hash, and returns a signed access token on success.

    Args:
        payload (LoginRequest): The login credentials, containing:
            - username (str): The user's unique username.
            - password (str): The user's plaintext password.
        db (Session): The injected SQLAlchemy session for PostgreSQL.

    Returns:
        TokenOut: A bearer token wrapper containing:
            - access_token (str): The signed JWT.
            - token_type (str): Always "bearer".

    Raises:
        HTTPException (401): If the username doesn't exist or the password
            doesn't match.
    """
    user = db.query(User).filter(User.username == payload.username).first()

    # We combine both checks so we don't reveal WHICH one failed
    # (otherwise an attacker could probe which usernames exist).
    if not user or not verify_password(payload.password, user.hashed_password):  # pyright: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        )

    token = create_access_token({"sub": str(user.id), "role": user.role})
    return TokenOut(access_token=token)


@auth.get("/profile", response_model=UserOut)
def profile(current_user: User = Depends(get_current_user)):
    """
    Return the currently authenticated user.

    Args:
        current_user (User): The user resolved from the bearer token
            by the get_current_user dependency.

    Returns:
        UserOut: The current user's public fields (id, username, role).

    Raises:
        HTTPException (401): If no valid bearer token is supplied
            (raised by the get_current_user dependency).
    """
    return current_user


@auth.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_postgresql_db),
    _: User = Depends(require_admin),
):
    """
    List every registered user. Admin-only.

    Args:
        db (Session): The injected SQLAlchemy session for PostgreSQL.
        _ (User): Unused; injected for its side effect of enforcing
            the Admin role requirement.

    Returns:
        list[UserOut]: All user records, serialized to their public fields.

    Raises:
        HTTPException (401): If the request is not authenticated.
        HTTPException (403): If the caller is not an Admin.
    """
    return db.query(User).all()


@auth.post("/users", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_postgresql_db),
    _: User = Depends(require_admin),
):
    """
    Create a new user. Admin-only.

    Hashes the supplied password before persisting. Usernames must be unique.

    Args:
        payload (UserCreate): The new user fields, containing:
            - username (str): The desired username; must be unique.
            - password (str): The plaintext password (will be hashed).
            - role (Literal["Admin", "User"]): The role to assign. Defaults to "User".
        db (Session): The injected SQLAlchemy session for PostgreSQL.
        _ (User): Unused; injected for its side effect of enforcing
            the Admin role requirement.

    Returns:
        UserOut: The newly created user's public fields.

    Raises:
        HTTPException (400): If the username is already taken.
        HTTPException (401): If the request is not authenticated.
        HTTPException (403): If the caller is not an Admin.
    """
    # We check that the username isn't already taken.
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="That username is already taken.")

    new_user = User(
        username=payload.username,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@auth.delete("/users/{user_id}", status_code=204)
def delete_user(
    user_id: int,
    db: Session = Depends(get_postgresql_db),
    current_user: User = Depends(require_admin),
):
    """
    Delete a user by ID. Admin-only.

    Admins are prevented from deleting their own account to avoid locking
    the system out.

    Args:
        user_id (int): The ID of the user to delete.
        db (Session): The injected SQLAlchemy session for PostgreSQL.
        current_user (User): The authenticated admin making the request.

    Returns:
        None: 204 No Content on success.

    Raises:
        HTTPException (400): If the admin tries to delete their own account.
        HTTPException (401): If the request is not authenticated.
        HTTPException (403): If the caller is not an Admin.
        HTTPException (404): If no user exists with the given ID.
    """
    # Prevent an admin from accidentally deleting their own account.
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="You cannot delete your own account."
        )

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")

    db.delete(user)
    db.commit()
