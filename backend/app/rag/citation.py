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
    if not chunks:
        return "(No relevant transcript passages were found.)"

    blocks = []

    for chunk in chunks:
        blocks.append(
            f"{format_inline(chunk)}\n{chunk.text}"
        )

    return "\n\n---\n\n".join(blocks)