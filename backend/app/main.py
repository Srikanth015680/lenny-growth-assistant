"""
FastAPI application entrypoint.

Startup initializes the database (section 6); every router is registered
under /api per the spec's endpoint paths; both AppError and any unhandled
exception are caught centrally so no route needs its own try/except just
to keep a stack trace off the wire (section 23).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import artifacts, chat, health, sessions
from app.config import settings
from app.database import init_db
from app.exceptions import AppError, app_error_handler, unhandled_exception_handler
from app.logging_config import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup", extra={"env": settings.app_env})
    await init_db()
    yield
    logger.info("app_shutdown")


app = FastAPI(title="The Lenny Growth Assistant", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.include_router(health.router, prefix="/api")
app.include_router(sessions.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(artifacts.router, prefix="/api")
