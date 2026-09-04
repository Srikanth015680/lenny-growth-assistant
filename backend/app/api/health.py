"""
GET /api/health — structured diagnostics (section 19, 24).

Every dependency is checked independently and reported independently; one
down component degrades the overall status but never crashes this endpoint
itself (this is the one route that must always respond, even when nothing
else is working, so ops/on-call can tell what's wrong).
"""
from fastapi import APIRouter

from app.config import settings
from app.database import check_db_health, check_pgvector_health
from app.models.schemas import HealthComponent, HealthOut
from app.providers.factory import get_provider

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    db_ok = await check_db_health()
    database = HealthComponent(
        status="ok" if db_ok else "down",
        detail=None if db_ok else "Could not reach PostgreSQL.",
    )

    if db_ok:
        vector_ok = await check_pgvector_health()
        pgvector = HealthComponent(
            status="ok" if vector_ok else "down",
            detail=None if vector_ok else "pgvector extension is not installed.",
        )
    else:
        pgvector = HealthComponent(status="down", detail="Skipped — database unreachable.")

    ollama_health = await get_provider("ollama").health_check()
    ollama = HealthComponent(status=ollama_health.status, detail=ollama_health.detail)

    if settings.anthropic_available:
        anthropic_health = await get_provider("anthropic").health_check()
        anthropic = HealthComponent(status=anthropic_health.status, detail=anthropic_health.detail)
    else:
        anthropic = HealthComponent(
            status="not_configured", detail="ANTHROPIC_API_KEY is not set."
        )

    application = HealthComponent(status="ok")

    critical = [database, pgvector]
    if any(c.status == "down" for c in critical):
        overall = "down"
    elif ollama.status != "ok" and anthropic.status != "ok":
        # No usable LLM provider at all is a real degradation, even though
        # the API itself is up.
        overall = "degraded"
    elif ollama.status != "ok" or anthropic.status == "down":
        overall = "degraded"
    else:
        overall = "ok"

    return HealthOut(
        status=overall,
        database=database,
        pgvector=pgvector,
        ollama=ollama,
        anthropic=anthropic,
        application=application,
    )
