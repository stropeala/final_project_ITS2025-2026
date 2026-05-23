from datetime import datetime, timedelta, timezone
from os import getenv

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.extensions import get_postgresql_db
from app.models import User

load_dotenv()

SECRET_KEY = getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. Check your .env file."
    )

ALGORITHM = getenv("ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60)
try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(ACCESS_TOKEN_EXPIRE_MINUTES)
except ValueError:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES environment variable must be an integer. Check your .env file."
    )
if ACCESS_TOKEN_EXPIRE_MINUTES <= 0:
    raise RuntimeError(
        "ACCESS_TOKEN_EXPIRE_MINUTES must be a positive integer. Check your .env file."
    )

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hashes a password using bcrypt.

    Args:
        plain_password (str): The user's password.

    Returns:
        str: The bcrypt hash that is safe to add to the database.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Checks a password against a stored bcrypt hash.

    Args:
        plain_password (str): The user's password at login.
        hashed_password (str): The bcrypt hash previously stored for the user.

    Returns:
        bool: True if the password matches the hash or False if not.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Builds a signed JWT access token with an expiry time.

    Adds an "exp" field to the payload set to ACCESS_TOKEN_EXPIRE_MINUTES from now
    then signs the token with SECRET_KEY using ALGORITHM.

    Args:
        data (dict): Data to embed in the token (e.g., {"sub": user_id, "role": role}).

    Returns:
        str: The encoded JWT, ready to send back to the client.
    """
    payload = data.copy()
    expiry_time = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES  # pyright: ignore
    )
    payload["exp"] = expiry_time

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)  # pyright: ignore


def decode_access_token(token: str) -> dict:
    """
    Verifies and decodes a JWT access token.

    Args:
        token (str): The raw JWT string from the Authorization header.

    Returns:
        dict: The decoded payload data if the token is valid.

    Raises:
        HTTPException (401): If the token is malformed, tampered with, or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # pyright: ignore
        return payload

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# HTTPBearer() tells FastAPI to extract that token string automatically.
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_db: Session = Depends(get_postgresql_db),
) -> User:
    """
    A FastAPI dependency function. Any route that lists this as a dependency
    will automatically require the caller to be logged in.

    Decodes the JWT, extracts the "sub" (subject) claim as the user ID, and loads
    the corresponding User row from PostgreSQL.

    Args:
        credentials (HTTPAuthorizationCredentials): Injected by FastAPI;
                contains the bearer token from the Authorization header.
        user_db (Session): The injected SQLAlchemy session for PostgreSQL.

    Returns:
        User: The authenticated user data.

    Raises:
        HTTPException (401): If the token is invalid, the user ID claim is missing
                            or non-numeric, or refers to a user that no longer exists.
    """

    # Decode the token string into a Python dict
    payload = decode_access_token(credentials.credentials)

    # "sub" (subject) is the standard JWT field for the user's identifier.
    # We stored the user ID here when we created the token.
    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is missing user ID.",
        )

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has an invalid user ID.",
        )

    # Look up the user in the database.
    # int(user_id) converts the string "5" back to the integer 5.
    user = user_db.query(User).filter(User.id == user_id_int).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer exists.",
        )

    return user


def require_role(*allowed_roles: str):
    """
    Factory that creates a role-checking FastAPI dependency.

    Returns a callable suitable for use with Depends(...). The returned
    dependency authenticates the user via get_current_user and then checks
    that their role is in the allowed set.

    Args:
        *allowed_roles (str): One or more role names that are permitted.
                            (e.g., "Admin").

    Returns:
        Callable[..., User]: A FastAPI dependency that yields the current user
                            when authorized.

    Raises:
        HTTPException (403): Raised by the returned dependency when the
                            current user's role is not in the allowed set.
    """

    # This inner function is the actual dependency FastAPI will call
    def check_role(current_user: User = Depends(get_current_user)) -> User:

        # Check if the logged-in user's role is in our allowed list
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(allowed_roles)}.",
            )
        # If the role is allowed, return the user so the route can use it
        return current_user

    return check_role


# Handy shortcuts – routes can write Depends(require_admin) instead of
# Depends(require_role("admin")) each time.
require_admin = require_role("Admin")
require_any = require_role("Admin", "User")
