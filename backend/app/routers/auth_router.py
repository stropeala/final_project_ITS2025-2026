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


@auth.get("/users", response_model=list[UserOut])
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


@auth.post("/users", response_model=UserOut, status_code=201)
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
    # We check that the username isn't already taken.
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


@auth.delete("/users/{user_id}", status_code=204)
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
