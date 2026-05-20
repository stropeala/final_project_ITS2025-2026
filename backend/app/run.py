from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.auth import seed_admin, seed_normal_user
from app.routers import admin_router, auth_router, chatbot_router, home_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan handler that runs startup and shutdown logic.

    On startup, seeds the PostgreSQL database with the default Admin and
    User accounts (no duplicates if they already exist). Control is then yielded
    to FastAPI for the duration of the application's lifetime.

    Args:
        app (FastAPI): The FastAPI application instance, supplied by the
            framework. Unused, but required by the lifespan protocol.

    Yields:
        None: Yields once after seeding completes; nothing is returned
        to the caller.
    """
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
chatbot_project.include_router(admin_router)
