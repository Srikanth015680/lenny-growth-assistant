"""
POST /api/chat — grounded RAG chat over SSE (sections 19, 20).

Validation and persistence happen as plain request/response work, so
failures there produce normal JSON error responses (via AppError ->
app_error_handler). Once the SSE stream actually starts, a failure can no
longer change the HTTP status code, so mid-stream errors are relayed as an
explicit `event: error` SSE event instead and the stream ends there
(section 25: "terminate stream gracefully").

mode dispatches to the matching agent/orchestrator.py coroutine
(default | ship30 | artifact). All three share the same validation,
persistence, and error-handling shell here — only the generator passed to
event_stream() differs.
"""
import json

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from starlette.responses import StreamingResponse

from app.agent.context import build_history
from app.agent.orchestrator import run_artifact, run_default_chat, run_ship30
from app.agent.router import resolve_mode
from app.config import settings
from app.database import get_db
from app.exceptions import AppError, InvalidMessageError, SessionNotFoundError
from app.logging_config import get_logger
from app.models.db_models import Artifact, Message, SessionModel
from app.models.schemas import ChatRequest
from app.providers.base import ChatTurn
from app.providers.factory import get_provider

router = APIRouter(tags=["chat"])
logger = get_logger(__name__)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/chat")
async def chat(payload: ChatRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    message_text = payload.message.strip()
    if not message_text:
        raise InvalidMessageError("Message cannot be empty.")
    if len(message_text) > settings.max_message_length:
        raise InvalidMessageError(
            f"Message exceeds the {settings.max_message_length} character limit."
        )

    result = await db.execute(
        select(SessionModel)
        .where(SessionModel.id == payload.session_id)
        .options(selectinload(SessionModel.messages))
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise SessionNotFoundError(f"No session found with id {payload.session_id}.")

    mode = resolve_mode(payload.mode, message_text)
    provider = get_provider(payload.provider)  # raises ProviderNotConfiguredError if invalid

    prior_history = build_history(session.messages)

    user_message = Message(session_id=session.id, role="user", content=message_text)
    db.add(user_message)
    await db.commit()

    full_history = prior_history + [ChatTurn(role="user", content=message_text)]

    if mode == "ship30":
        generator = run_ship30(
            db=db, provider=provider, query=message_text, history=full_history
        )
    elif mode == "artifact":
        generator = run_artifact(
            db=db,
            provider=provider,
            query=message_text,
            history=full_history,
            artifact_type=payload.artifact_type,
        )
    else:
        generator = run_default_chat(
            db=db, provider=provider, query=message_text, history=full_history
        )

    async def event_stream():
        try:
            final_content = ""
            final_sources: list[dict] = []
            final_artifact: dict | None = None

            async for chat_event in generator:
                if chat_event["event"] == "_final":
                    final_content = chat_event["data"]["content"]
                    final_sources = chat_event["data"]["sources"]
                    final_artifact = chat_event["data"].get("artifact")
                    continue
                yield _sse(chat_event["event"], chat_event["data"])

            assistant_message = Message(
                session_id=session.id,
                role="assistant",
                content=final_content,
                sources=final_sources or None,
            )
            db.add(assistant_message)
            await db.commit()

            if final_artifact:
                artifact_row = Artifact(
                    message_id=assistant_message.id,
                    artifact_type=final_artifact["type"],
                    title=final_artifact["title"],
                    content=final_artifact["content"],
                )
                db.add(artifact_row)
                await db.commit()

            yield _sse("done", {"message_id": str(assistant_message.id)})
        except AppError as exc:
            logger.warning("chat_stream_app_error", extra={"error_code": exc.code})
            yield _sse("error", {"error": {"code": exc.code, "message": exc.message}})
        except Exception as exc:  # noqa: BLE001 — never let a raw traceback reach the client
            logger.error(
                "chat_stream_unhandled_error",
                extra={"exception_type": type(exc).__name__},
                exc_info=exc,
            )
            yield _sse(
                "error",
                {"error": {"code": "INTERNAL_ERROR", "message": "The response stream failed."}},
            )

    return StreamingResponse(event_stream(), media_type="text/event-stream")
