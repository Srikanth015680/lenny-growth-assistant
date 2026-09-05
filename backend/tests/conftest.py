import os
import random

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/lenny_growth_assistant_test",
)
os.environ.setdefault("OLLAMA_BASE_URL", "http://localhost:11434")
os.environ.setdefault("CORS_ORIGINS", "http://localhost:3000")

from app.models.db_models import Base


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_schema():
    from app.database import engine

    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
    yield

    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                "TRUNCATE TABLE artifacts, messages, sessions, "
                "transcript_chunks CASCADE"
            )
        )
        await session.commit()


@pytest_asyncio.fixture
async def client():
    from app.main import app

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture
async def db_session():
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session


def random_embedding(dim: int = 384, seed: int | None = None) -> list[float]:
    rng = random.Random(seed)

    vector = [rng.uniform(-1, 1) for _ in range(dim)]
    norm = sum(value * value for value in vector) ** 0.5

    return [value / norm for value in vector]