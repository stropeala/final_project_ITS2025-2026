from fastapi import FastAPI

from app.routers import chatbot_router, home_router

# Initialiaze the FastAPI app.
chatbot_project = FastAPI(
    title="Project_ITS",
    version="beta",
)

# Add routers to the app.
chatbot_project.include_router(home_router)
chatbot_project.include_router(chatbot_router)
