"""
Session CRUD (section 19): POST /api/sessions, GET /api/sessions,
GET /api/sessions/{session_id}.

This router has no dependency on any LLM provider or the RAG pipeline, so
it's fully functional and testable on its own — see tests/test_sessions.py.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.exceptions import SessionNotFoundError
from app.models.db_models import Message, SessionModel
from app.models.schemas import SessionCreate, SessionDetailOut, SessionOut

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionOut, status_code=201)
async def create_session(
    payload: SessionCreate, db: AsyncSession = Depends(get_db)
) -> SessionModel:
    session = SessionModel(title=payload.title or "New conversation")
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("", response_model=list[SessionOut])
async def list_sessions(db: AsyncSession = Depends(get_db)) -> list[SessionModel]:
    result = await db.execute(select(SessionModel).order_by(SessionModel.updated_at.desc()))
    return list(result.scalars().all())


@router.get("/{session_id}", response_model=SessionDetailOut)
async def get_session(session_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> SessionModel:
    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.id == session_id)
        .options(selectinload(SessionModel.messages).selectinload(Message.artifacts))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise SessionNotFoundError(f"No session found with id {session_id}.")
    return session
