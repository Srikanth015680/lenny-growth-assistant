"""
Markdown / HTML artifact generation skill (section 16).

Produces the structured artifact dict the API persists as an Artifact row
and the frontend renders in the sandboxed viewer (sections 17-18). Same
grounding contract as the Ship30 skill: no retrieved context, no artifact —
callers get InsufficientContextError instead of a fabricated document.
"""
import re

from app.exceptions import ArtifactGenerationError, InsufficientContextError
from app.providers.base import BaseLLMProvider, ChatTurn
from app.rag.artifact_prompts import build_artifact_system_prompt
from app.rag.prompts import INSUFFICIENT_CONTEXT_FALLBACK
from app.rag.retriever import RetrievedChunk

_MD_FENCE_RE = re.compile(r"^```(?:markdown|md)?\n(.*)\n```$", re.DOTALL)


def _strip_wrapping_code_fence(text: str) -> str:
    """Defensive cleanup: the prompt tells the model not to wrap output in
    a code fence, but models don't always listen."""
    match = _MD_FENCE_RE.match(text.strip())
    return match.group(1) if match else text.strip()


def _default_title(topic: str, artifact_type: str) -> str:
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

    system_prompt = build_artifact_system_prompt(artifact_type, chunks)
    raw = await provider.generate_response(
        system_prompt=system_prompt,
        history=[ChatTurn(role="user", content=f"Generate the artifact now. Topic: {topic}")],
    )

    if artifact_type == "markdown":
        content = _strip_wrapping_code_fence(raw)
    else:
        content = raw.strip()
        if not content.lower().startswith(("<!doctype", "<html")):
            raise ArtifactGenerationError(
                "Generated content was not a valid standalone HTML document."
            )

    if not content:
        raise ArtifactGenerationError("The provider returned an empty artifact.")

    return {
        "type": artifact_type,
        "title": _default_title(topic, artifact_type),
        "content": content,
    }
