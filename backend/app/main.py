"""
Main FastAPI application.

This is where the app starts up, sets up the database, middleware,
error handling, and API routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import artifacts, chat, health, sessions
from app.config import settings
from app.database import init_db
from app.exceptions import (
    AppError,
    app_error_handler,
    unhandled_exception_handler,
)
from app.logging_config import configure_logging, get_logger


configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run setup when the app starts and cleanup when it shuts down."""

    logger.info(
        "app_startup",
        extra={"env": settings.app_env},
    )

    await init_db()

    yield

    logger.info("app_shutdown")


app = FastAPI(
    title="The Lenny Growth Assistant",
    version="0.1.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Keep application errors in one place so every API response
# follows the same format.
app.add_exception_handler(AppError, app_error_handler)

# Catch anything unexpected without exposing the actual exception
# or stack trace to the client.
app.add_exception_handler(Exception, unhandled_exception_handler)


# All API routes live under /api.
app.include_router(health.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(artifacts.router, prefix="/api")