from app.exceptions import InsufficientContextError
from app.providers.base import BaseLLMProvider, ChatTurn
from app.rag.prompts import INSUFFICIENT_CONTEXT_FALLBACK
from app.rag.retriever import RetrievedChunk
from app.rag.ship30_prompts import build_ship30_system_prompt


async def write_ship30_essay(
    topic: str,
    chunks: list[RetrievedChunk],
    provider: BaseLLMProvider,
) -> str:
    if not chunks:
        raise InsufficientContextError(
            INSUFFICIENT_CONTEXT_FALLBACK
        )

    system_prompt = build_ship30_system_prompt(
        topic,
        chunks,
    )

    history = [
        ChatTurn(
            role="user",
            content=f"Write the essay now. Topic: {topic}",
        )
    ]

    return await provider.generate_response(
        system_prompt=system_prompt,
        history=history,
    )