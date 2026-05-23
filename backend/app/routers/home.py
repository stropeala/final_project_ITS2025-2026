from fastapi import APIRouter

# Initialize Home router.
home = APIRouter(tags=["Home"])


# GET or POST url paths for router.
@home.get("/")
async def index():
    """
    Checks the Homepage router.

    Args:
        None.

    Returns:
        dict: A placeholder message.
    """
    return {
        "message": "Project is working...",
    }
