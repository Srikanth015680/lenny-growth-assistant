"""
GET /api/artifacts/{artifact_id} (section 19).

Writing artifacts happens as a side effect of /api/chat in "artifact" mode
(see skills/artifact_generator.py, wired up in a later phase) — this router
only covers reading one back, e.g. for a shareable link or a page refresh.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import AppError
from app.models.db_models import Artifact
from app.models.schemas import ArtifactOut

router = APIRouter(prefix="/artifacts", tags=["artifacts"])


class ArtifactNotFoundError(AppError):
    code = "ARTIFACT_NOT_FOUND"
    http_status = 404


@router.get("/{artifact_id}", response_model=ArtifactOut)
async def get_artifact(artifact_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> Artifact:
    result = await db.execute(select(Artifact).where(Artifact.id == artifact_id))
    artifact = result.scalar_one_or_none()
    if artifact is None:
        raise ArtifactNotFoundError(f"No artifact found with id {artifact_id}.")
    return artifact
