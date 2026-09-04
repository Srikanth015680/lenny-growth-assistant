"""
Orchestrator — ties retrieval, the grounding prompt, and a provider
together into the event stream /api/chat relays as SSE (section 20).

Each `run_*` coroutine is an async generator of plain dicts shaped like
{"event": "...", "data": {...}}; api/chat.py is the only place that knows
how to serialize that into actual SSE wire format. Keeping that
serialization out of this module means orchestrator.py stays testable
without spinning up a real HTTP response.

The internal "_final" event carries whatever chat.py needs to persist
after the stream ends (assistant message content, sources, and — for
ship30/artifact modes — a generated artifact) without leaking persistence
concerns into this module.
"""
from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import BaseLLMProvider
from app.rag.citation import to_source_citation
from app.rag.prompts import build_system_prompt
from app.rag.retriever import TranscriptRetriever
from app.skills.artifact_generator import generate_artifact
from app.skills.ship30_writer import write_ship30_essay

ChatEvent = dict


async def run_default_chat(
    *,
    db: AsyncSession,
    provider: BaseLLMProvider,
    query: str,
    history,
) -> AsyncIterator[ChatEvent]:
    yield {"event": "status", "data": {"message": "Searching transcripts"}}

    retriever = TranscriptRetriever(db)
    chunks = await retriever.retrieve_relevant_chunks(query)

    sources = [to_source_citation(c).model_dump() for c in chunks]
    yield {"event": "sources", "data": {"sources": sources}}

    system_prompt = build_system_prompt(chunks)

    yield {"event": "status", "data": {"message": "Generating response"}}

    full_text_parts: list[str] = []
    async for token in provider.stream_response(system_prompt=system_prompt, history=history):
        full_text_parts.append(token)
        yield {"event": "token", "data": {"content": token}}

    yield {
        "event": "_final",  # internal marker, not sent over the wire — see api/chat.py
        "data": {"content": "".join(full_text_parts), "sources": sources},
    }


async def run_ship30(
    *,
    db: AsyncSession,
    provider: BaseLLMProvider,
    query: str,
    history,
) -> AsyncIterator[ChatEvent]:
    yield {"event": "status", "data": {"message": "Searching transcripts"}}

    retriever = TranscriptRetriever(db)
    chunks = await retriever.retrieve_relevant_chunks(query)
    sources = [to_source_citation(c).model_dump() for c in chunks]
    yield {"event": "sources", "data": {"sources": sources}}

    yield {"event": "status", "data": {"message": "Writing Ship 30 essay"}}
    essay = await write_ship30_essay(query, chunks, provider)

    artifact = {"type": "markdown", "title": f"Ship 30 Essay: {query}"[:255], "content": essay}
    yield {"event": "artifact", "data": artifact}

    reply = f"I've drafted a Ship 30 for 30-style essay on this — see the artifact panel."
    yield {
        "event": "_final",
        "data": {"content": reply, "sources": sources, "artifact": artifact},
    }


async def run_artifact(
    *,
    db: AsyncSession,
    provider: BaseLLMProvider,
    query: str,
    history,
    artifact_type: str = "markdown",
) -> AsyncIterator[ChatEvent]:
    yield {"event": "status", "data": {"message": "Searching transcripts"}}

    retriever = TranscriptRetriever(db)
    chunks = await retriever.retrieve_relevant_chunks(query)
    sources = [to_source_citation(c).model_dump() for c in chunks]
    yield {"event": "sources", "data": {"sources": sources}}

    yield {"event": "status", "data": {"message": f"Generating {artifact_type} artifact"}}
    artifact = await generate_artifact(artifact_type, query, chunks, provider)
    yield {"event": "artifact", "data": artifact}

    reply = f"I've put together a {artifact_type} artifact for this — see the panel."
    yield {
        "event": "_final",
        "data": {"content": reply, "sources": sources, "artifact": artifact},
    }
