from fastapi import FastAPI

from .routers import chatbot_router, home_router

chatbot_project = FastAPI(
    title="Project_ITS",
    version="beta",
)

chatbot_project.include_router(home_router)
chatbot_project.include_router(chatbot_router)
