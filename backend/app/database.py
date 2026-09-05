import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.exceptions import DatabaseUnavailableError
from app.logging_config import get_logger
from app.models.db_models import Base


logger = get_logger(__name__)

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db(
    retries: int = 5,
    delay_seconds: float = 2.0,
) -> None:
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text("CREATE EXTENSION IF NOT EXISTS vector")
                )
                await conn.run_sync(Base.metadata.create_all)

            logger.info(
                "db_init_complete",
                extra={"attempt": attempt},
            )
            return

        except Exception as exc:  # Retry if the database is not ready yet.
            last_error = exc

            logger.warning(
                "db_init_retry",
                extra={
                    "attempt": attempt,
                    "retries": retries,
                    "error": str(exc),
                },
            )

            await asyncio.sleep(delay_seconds)

    raise DatabaseUnavailableError(
        f"Could not initialize the database after {retries} attempts: {last_error}"
    )


async def check_db_health() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def check_pgvector_health() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text(
                    "SELECT 1 FROM pg_extension "
                    "WHERE extname = 'vector'"
                )
            )
            return result.first() is not None
    except Exception:
        return False