from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth import seed_admin, seed_normal_user
from app.routers import auth_router, chatbot_router, home_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Seeding database...")
    seed_admin()
    seed_normal_user()
    yield


# Initialiaze the FastAPI app.
chatbot_project = FastAPI(
    title="Project_ITS",
    version="beta",
    lifespan=lifespan,
)

# Add routers to the app.
chatbot_project.include_router(home_router)
chatbot_project.include_router(chatbot_router)
chatbot_project.include_router(auth_router)
