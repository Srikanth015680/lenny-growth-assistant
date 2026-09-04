"""
Shared pytest fixtures.

Uses a real Postgres+pgvector test database (created once per test session,
tables created/dropped around it) rather than mocking the DB layer itself —
SQLAlchemy async + pgvector's HNSW index + custom operators are exactly the
kind of thing that looks right and isn't, so this suite exercises them for
real. External LLM calls (Ollama over HTTP, Anthropic's SDK) and the
embedding model are mocked, per section 26 ("don't depend on a live Ollama
server or paid API").
"""
import asyncio
import os
import uuid

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_growth_assistant_test",
)
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings
from app.models.db_models import Base


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _prepare_schema():
    from sqlalchemy import text

    from app.database import engine as app_engine

    async with app_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Dispose the app's own engine (not a separate one) so every connection
    # this test session opened is closed cleanly before the session-scoped
    # event loop shuts down.
    await app_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def _clean_tables():
    """Truncate all tables between tests so they don't leak state, without
    paying the cost of dropping/recreating the schema (and its HNSW index)
    every single test."""
    from sqlalchemy import text

    from app.database import AsyncSessionLocal

    yield
    async with AsyncSessionLocal() as session:
        for table in ("artifacts", "messages", "sessions", "transcript_chunks"):
            await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
        await session.commit()


@pytest_asyncio.fixture
async def client():
    from app.main import app

    # The app's own lifespan calls init_db() again on startup, which is
    # harmless (CREATE EXTENSION IF NOT EXISTS / CREATE TABLE already exist)
    # — this keeps the test app wired exactly like production.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session


def random_embedding(dim: int = 384, seed: int | None = None) -> list[float]:
    import random

    rng = random.Random(seed)
    vec = [rng.uniform(-1, 1) for _ in range(dim)]
    norm = sum(v * v for v in vec) ** 0.5
    return [v / norm for v in vec]
