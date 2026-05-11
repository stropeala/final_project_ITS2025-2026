from fastapi import APIRouter

home = APIRouter(tags=["Home"])


@home.get("/")
def index():
    return {
        "message": "Project is working, kinda...",
    }
