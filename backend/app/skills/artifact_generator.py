import re

from app.exceptions import ArtifactGenerationError, InsufficientContextError
from app.providers.base import BaseLLMProvider, ChatTurn
from app.rag.artifact_prompts import build_artifact_system_prompt
from app.rag.prompts import INSUFFICIENT_CONTEXT_FALLBACK
from app.rag.retriever import RetrievedChunk


MD_FENCE_RE = re.compile(
    r"^```(?:markdown|md)?\n(.*)\n```$",
    re.DOTALL,
)


def strip_code_fence(text: str) -> str:
    """Remove markdown code fences if the model adds them."""
    text = text.strip()

    match = MD_FENCE_RE.match(text)
    if match:
        return match.group(1).strip()

    return text


def get_title(topic: str, artifact_type: str) -> str:
    label = "One-pager" if artifact_type == "html" else "Notes"
    return f"{label}: {topic}"[:255]


async def generate_artifact(
    artifact_type: str,
    topic: str,
    chunks: list[RetrievedChunk],
    provider: BaseLLMProvider,
) -> dict:
    if not chunks:
        raise InsufficientContextError(INSUFFICIENT_CONTEXT_FALLBACK)

    system_prompt = build_artifact_system_prompt(
        artifact_type,
        chunks,
    )

    history = [
        ChatTurn(
            role="user",
            content=f"Generate the artifact now. Topic: {topic}",
        )
    ]

    raw_content = await provider.generate_response(
        system_prompt=system_prompt,
        history=history,
    )

    if artifact_type == "markdown":
        content = strip_code_fence(raw_content)
    else:
        content = raw_content.strip()

        if not content.lower().startswith(("<!doctype", "<html")):
            raise ArtifactGenerationError(
                "Generated content was not a valid standalone HTML document."
            )

    if not content:
        raise ArtifactGenerationError(
            "The provider returned an empty artifact."
        )

    return {
        "type": artifact_type,
        "title": get_title(topic, artifact_type),
        "content": content,
    }