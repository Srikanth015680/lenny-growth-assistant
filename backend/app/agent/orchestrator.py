"""
Application orchestration for chat and artifact generation.

The orchestrator coordinates three things:

- retrieving relevant transcript context
- asking the selected LLM provider to generate a response
- emitting events that the API layer can expose over SSE

It deliberately does not know anything about HTTP or database persistence
beyond the session it needs for retrieval.

The API layer converts these events into SSE responses and handles saving
the final assistant message and generated artifacts.
"""

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.providers.base import BaseLLMProvider
from app.rag.citation import to_source_citation
from app.rag.prompts import build_system_prompt
from app.rag.retriever import TranscriptRetriever
from app.skills.artifact_generator import generate_artifact
from app.skills.ship30_writer import write_ship30_essay


ChatEvent = dict[str, Any]


async def run_default_chat(
    *,
    db: AsyncSession,
    provider: BaseLLMProvider,
    query: str,
    history: list,
) -> AsyncIterator[ChatEvent]:
    """
    Run a normal grounded chat request.

    Flow:

        retrieve -> send sources -> build prompt -> stream response

    The final event is internal and is consumed by the API layer for
    persistence. It is never sent directly to the client.
    """

    yield {
        "event": "status",
        "data": {"message": "Searching transcripts"},
    }

    retriever = TranscriptRetriever(db)
    chunks = await retriever.retrieve_relevant_chunks(query)

    sources = [
        to_source_citation(chunk).model_dump()
        for chunk in chunks
    ]

    yield {
        "event": "sources",
        "data": {"sources": sources},
    }

    system_prompt = build_system_prompt(chunks)

    yield {
        "event": "status",
        "data": {"message": "Generating response"},
    }

    response_parts: list[str] = []

    async for token in provider.stream_response(
        system_prompt=system_prompt,
        history=history,
    ):
        response_parts.append(token)

        yield {
            "event": "token",
            "data": {"content": token},
        }

    yield {
        "event": "_final",
        "data": {
            "content": "".join(response_parts),
            "sources": sources,
        },
    }


async def run_ship30(
    *,
    db: AsyncSession,
    provider: BaseLLMProvider,
    query: str,
    history: list,
) -> AsyncIterator[ChatEvent]:
    """
    Generate a grounded Ship 30-style essay.

    Retrieval happens before generation. If there is no usable transcript
    context, the Ship 30 skill raises InsufficientContextError rather than
    allowing the model to invent supporting material.
    """

    yield {
        "event": "status",
        "data": {"message": "Searching transcripts"},
    }

    retriever = TranscriptRetriever(db)
    chunks = await retriever.retrieve_relevant_chunks(query)

    sources = [
        to_source_citation(chunk).model_dump()
        for chunk in chunks
    ]

    yield {
        "event": "sources",
        "data": {"sources": sources},
    }

    yield {
        "event": "status",
        "data": {"message": "Writing Ship 30 essay"},
    }

    essay = await write_ship30_essay(
        query,
        chunks=chunks,
        provider=provider,
    )

    artifact = {
        "type": "markdown",
        "title": f"Ship 30 Essay: {query}"[:255],
        "content": essay,
    }

    yield {
        "event": "artifact",
        "data": artifact,
    }

    reply = (
        "I've drafted a Ship 30 for 30-style essay on this. "
        "You can view it in the artifact panel."
    )

    yield {
        "event": "_final",
        "data": {
            "content": reply,
            "sources": sources,
            "artifact": artifact,
        },
    }


async def run_artifact(
    *,
    db: AsyncSession,
    provider: BaseLLMProvider,
    query: str,
    history: list,
    artifact_type: str = "markdown",
) -> AsyncIterator[ChatEvent]:
    """
    Generate a grounded artifact.

    Supported artifact types are validated by the skill layer rather than
    trusting arbitrary values from the HTTP request.
    """

    yield {
        "event": "status",
        "data": {"message": "Searching transcripts"},
    }

    retriever = TranscriptRetriever(db)
    chunks = await retriever.retrieve_relevant_chunks(query)

    sources = [
        to_source_citation(chunk).model_dump()
        for chunk in chunks
    ]

    yield {
        "event": "sources",
        "data": {"sources": sources},
    }

    yield {
        "event": "status",
        "data": {
            "message": f"Generating {artifact_type} artifact",
        },
    }

    artifact = await generate_artifact(
        artifact_type,
        query,
        chunks,
        provider,
    )

    yield {
        "event": "artifact",
        "data": artifact,
    }

    reply = (
        f"I've put together a {artifact_type} artifact for this. "
        "You can view it in the artifact panel."
    )

    yield {
        "event": "_final",
        "data": {
            "content": reply,
            "sources": sources,
            "artifact": artifact,
        },
    }