"""
Ship 30 for 30-style essay generation skill (section 15).

A dedicated, reusable skill module — not a prompt inline in the API route —
so the structural rules (hook, headings, word count, grounding) live in one
tested place. Grounding is enforced the same way plain chat is: if
retrieval found nothing usable, this raises InsufficientContextError
instead of asking the provider to write ~1,250 words about nothing.
"""
from app.exceptions import InsufficientContextError
from app.providers.base import BaseLLMProvider, ChatTurn
from app.rag.prompts import INSUFFICIENT_CONTEXT_FALLBACK
from app.rag.retriever import RetrievedChunk
from app.rag.ship30_prompts import build_ship30_system_prompt


async def write_ship30_essay(
    topic: str, chunks: list[RetrievedChunk], provider: BaseLLMProvider
) -> str:
    if not chunks:
        raise InsufficientContextError(INSUFFICIENT_CONTEXT_FALLBACK)

    system_prompt = build_ship30_system_prompt(topic, chunks)
    return await provider.generate_response(
        system_prompt=system_prompt,
        history=[ChatTurn(role="user", content=f"Write the essay now. Topic: {topic}")],
    )
