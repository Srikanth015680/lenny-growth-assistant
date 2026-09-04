"""
Artifact skill + endpoint tests (section 26): generation (markdown/html,
including the insufficient-context refusal and malformed-HTML rejection),
and reading a persisted artifact back via the API.
"""
import uuid

import pytest

from app.exceptions import ArtifactGenerationError, InsufficientContextError
from app.rag.retriever import RetrievedChunk
from app.skills.artifact_generator import generate_artifact


class _FakeProvider:
    name = "fake"

    def __init__(self, reply: str):
        self.reply = reply

    async def generate_response(self, *, system_prompt, history):
        return self.reply

    async def stream_response(self, *, system_prompt, history):
        yield self.reply

    async def health_check(self):
        raise NotImplementedError


_CHUNK = RetrievedChunk(
    episode="Ep 1", guest="Guest 1", timestamp="10:00", text="Activation matters.", score=0.9
)


async def test_generate_markdown_artifact_strips_wrapping_code_fence():
    provider = _FakeProvider("```markdown\n# Notes\n\nSome content.\n```")
    artifact = await generate_artifact("markdown", "activation", [_CHUNK], provider)

    assert artifact["type"] == "markdown"
    assert artifact["content"] == "# Notes\n\nSome content."
    assert "activation" in artifact["title"].lower()


async def test_generate_html_artifact_accepts_valid_document():
    provider = _FakeProvider("<!DOCTYPE html><html><body>Hi</body></html>")
    artifact = await generate_artifact("html", "one-pager", [_CHUNK], provider)

    assert artifact["type"] == "html"
    assert artifact["content"].startswith("<!DOCTYPE html>")


async def test_generate_html_artifact_rejects_non_html_output():
    provider = _FakeProvider("Sure, here's your one-pager: ...")
    with pytest.raises(ArtifactGenerationError):
        await generate_artifact("html", "one-pager", [_CHUNK], provider)


async def test_generate_artifact_raises_when_no_context():
    with pytest.raises(InsufficientContextError):
        await generate_artifact("markdown", "activation", [], _FakeProvider("irrelevant"))


async def test_get_nonexistent_artifact_returns_structured_404(client):
    resp = await client.get(f"/api/artifacts/{uuid.uuid4()}")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "ARTIFACT_NOT_FOUND"
