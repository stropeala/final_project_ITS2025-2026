from typing import Literal

from pydantic import BaseModel


class LoginRequest(BaseModel):
    """
    Request body for the "/auth/login" endpoint.

    Attributes:
        username (str): The user's unique username.
        password (str): The user's plaintext password, verified against the
                        stored bcrypt hash by the login handler.
    """

    username: str
    password: str


class UserCreate(BaseModel):
    """
    Used to register a new account. The password is hashed before storage.

    Attributes:
        username (str): The desired username; must be unique.
        password (str): The plaintext password to hash and store.
        role (Literal["Admin", "User"]): The role to assign. Defaults to "User".
    """

    username: str
    password: str
    role: Literal["Admin", "User"] = "User"


class TokenOut(BaseModel):
    """
    Response body returned by "/auth/login" after successful authentication.

    Attributes:
        access_token (str): The signed JWT to send back on subsequent
                            requests as a bearer token.
        token_type (str): The token scheme. Always "bearer".
    """

    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """
    Public, response-safe view of a User data.
    Omits sensitive fields (e.g., hashed_password).

    Attributes:
        id (int): The user's database ID.
        username (str): The user's unique username.
        role (Literal["Admin", "User"]): The user's assigned role.
    """

    id: int
    username: str
    role: Literal["Admin", "User"]

    class Config:
        from_attributes = True
