"""
Pydantic v2 request/response schemas for the API layer.

Kept separate from db_models.py deliberately: ORM models describe storage,
these describe the wire contract. They're allowed to diverge (e.g. we never
want to accidentally serialize an internal-only column to a client).
"""
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ChatMode = Literal["default", "ship30", "artifact"]
LLMProvider = Literal["ollama", "anthropic"]
Role = Literal["user", "assistant", "system"]
ArtifactType = Literal["markdown", "html"]


class SourceCitation(BaseModel):
    episode: str
    guest: str | None = None
    timestamp: str | None = None
    text: str
    score: float


class SessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255)


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ArtifactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    message_id: uuid.UUID
    artifact_type: ArtifactType
    title: str
    content: str
    created_at: datetime


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: Role
    content: str
    sources: list[SourceCitation] | None = None
    created_at: datetime
    artifacts: list[ArtifactOut] = Field(default_factory=list)


class SessionDetailOut(SessionOut):
    messages: list[MessageOut] = Field(default_factory=list)


class ChatRequest(BaseModel):
    session_id: uuid.UUID
    message: str = Field(min_length=1)
    provider: LLMProvider | None = None
    mode: ChatMode = "default"
    # Only consulted when mode == "artifact"; defaults to markdown so the
    # frontend can omit it for the common case and only send it when the
    # user explicitly picks HTML.
    artifact_type: ArtifactType = "markdown"


class HealthComponent(BaseModel):
    status: Literal["ok", "degraded", "down", "not_configured"]
    detail: str | None = None


class HealthOut(BaseModel):
    status: Literal["ok", "degraded", "down"]
    database: HealthComponent
    pgvector: HealthComponent
    ollama: HealthComponent
    anthropic: HealthComponent
    application: HealthComponent


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
