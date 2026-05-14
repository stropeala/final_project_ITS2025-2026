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

SECRET_KEY = getenv("SECRET_KEY", "super-secret-key69")
ALGORITHM = getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        plain_password (str): The user-provided password.

    Returns:
        str: The bcrypt hash, safe to add to the database.
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check a password against a stored bcrypt hash.

    Args:
        plain_password (str): The password supplied at login.
        hashed_password (str): The bcrypt hash previously stored for the user.

    Returns:
        bool: True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict) -> str:
    """
    Build a signed JWT access token with an expiry claim.

    Adds an "exp" field to the payload set to ACCESS_TOKEN_EXPIRE_MINUTES
    from now (UTC), then signs the token with SECRET_KEY using ALGORITHM.

    Args:
        data (dict): Claims to embed in the token (e.g., {"sub": user_id, "role": role}).

    Returns:
        str: The encoded JWT, ready to send back to the client.
    """
    payload = data.copy()
    expiry_time = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload["exp"] = expiry_time

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Verify and decode a JWT access token.

    Args:
        token (str): The raw JWT string from the Authorization header.

    Returns:
        dict: The decoded payload claims if the token is valid.

    Raises:
        HTTPException (401): If the token is malformed, tampered with, or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )


bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_postgresql_db),
) -> User:
    """
    Resolve the authenticated User from the bearer token in the request.

    Decodes the JWT, extracts the "sub" claim as the user ID, and loads
    the corresponding User row from PostgreSQL.

    Args:
        credentials (HTTPAuthorizationCredentials): Injected by FastAPI;
            contains the bearer token from the Authorization header.
        db (Session): The injected SQLAlchemy session for PostgreSQL.

    Returns:
        User: The authenticated user record.

    Raises:
        HTTPException (401): If the token is invalid, missing a user ID,
            or refers to a user that no longer exists.
    """
    payload = decode_access_token(credentials.credentials)

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(status_code=401, detail="Token is missing user ID.")

    user = db.query(User).filter(User.id == int(user_id)).first()

    if user is None:
        raise HTTPException(status_code=401, detail="User account no longer exists.")

    return user


def require_role(*allowed_roles: str):
    """
    Build a FastAPI dependency that enforces role-based access control.

    Returns a callable suitable for use with Depends(...). The returned
    dependency authenticates the user via get_current_user and then checks
    that their role is in the allowed set.

    Args:
        *allowed_roles (str): One or more role names that are permitted.
            Casing must match what is stored on the User row (e.g., "Admin").

    Returns:
        Callable[..., User]: A FastAPI dependency that yields the current user
        when authorized.

    Raises:
        HTTPException (403): Raised by the returned dependency when the
            current user's role is not in the allowed set.
    """

    def check_role(current_user: User = Depends(get_current_user)) -> User:

        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {' or '.join(allowed_roles)}.",
            )

        return current_user

    return check_role


require_admin = require_role("Admin")
require_any = require_role("Admin", "User")
