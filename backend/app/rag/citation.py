"""
Formatting retrieved chunks into citations (section 10).

Two representations of the same data:
  - `format_inline` — human-readable "[Episode — Guest — Timestamp]" string
    for the LLM prompt / for a plain-text rendering.
  - `to_source_citation` — structured dict matching the SourceCitation
    schema, persisted as JSONB on the message and rendered as source
    cards/badges by the frontend.
"""
from app.models.schemas import SourceCitation
from app.rag.retriever import RetrievedChunk


def format_inline(chunk: RetrievedChunk) -> str:
    parts = [chunk.episode]
    if chunk.guest:
        parts.append(chunk.guest)
    if chunk.timestamp:
        parts.append(chunk.timestamp)
    return f"[{' — '.join(parts)}]"


def to_source_citation(chunk: RetrievedChunk) -> SourceCitation:
    return SourceCitation(
        episode=chunk.episode,
        guest=chunk.guest,
        timestamp=chunk.timestamp,
        text=chunk.text,
        score=chunk.score,
    )


def format_context_block(chunks: list[RetrievedChunk]) -> str:
    """Renders retrieved chunks as the CONTEXT block injected into the
    system prompt. Each chunk is tagged with its citation up front so the
    model can attribute claims without a separate lookup step."""
    if not chunks:
        return "(No transcript passages met the relevance threshold for this query.)"

    blocks = []
    for chunk in chunks:
        blocks.append(f"{format_inline(chunk)}\n{chunk.text}")
    return "\n\n---\n\n".join(blocks)
