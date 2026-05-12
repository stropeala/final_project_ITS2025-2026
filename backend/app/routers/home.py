from fastapi import APIRouter

# Initialize Home router
home = APIRouter(tags=["Home"])


# GET or POST url paths for home router
@home.get("/")
def index():
    """PLACEHOLDER index page"""
    return {
        "message": "Project is working, kinda...",
    }
