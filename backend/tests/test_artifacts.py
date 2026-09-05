import uuid

import pytest

from app.exceptions import (
    ArtifactGenerationError,
    InsufficientContextError,
)
from app.rag.retriever import RetrievedChunk
from app.skills.artifact_generator import generate_artifact


class FakeProvider:
    name = "fake"

    def __init__(self, reply: str):
        self.reply = reply

    async def generate_response(self, *, system_prompt, history):
        return self.reply

    async def stream_response(self, *, system_prompt, history):
        yield self.reply

    async def health_check(self):
        raise NotImplementedError


CHUNK = RetrievedChunk(
    episode="Ep 1",
    guest="Guest 1",
    timestamp="10:00",
    text="Activation matters.",
    score=0.9,
)


async def test_generate_markdown_artifact_strips_code_fence():
    provider = FakeProvider(
        "```markdown\n# Notes\n\nSome content.\n```"
    )

    artifact = await generate_artifact(
        "markdown",
        "activation",
        [CHUNK],
        provider,
    )

    assert artifact["type"] == "markdown"
    assert artifact["content"] == "# Notes\n\nSome content."
    assert "activation" in artifact["title"].lower()


async def test_generate_html_artifact_accepts_valid_document():
    provider = FakeProvider(
        "<!DOCTYPE html><html><body>Hi</body></html>"
    )

    artifact = await generate_artifact(
        "html",
        "one-pager",
        [CHUNK],
        provider,
    )

    assert artifact["type"] == "html"
    assert artifact["content"].startswith("<!DOCTYPE html>")


async def test_generate_html_artifact_rejects_invalid_output():
    provider = FakeProvider(
        "Sure, here's your one-pager: ..."
    )

    with pytest.raises(ArtifactGenerationError):
        await generate_artifact(
            "html",
            "one-pager",
            [CHUNK],
            provider,
        )


async def test_generate_artifact_requires_context():
    provider = FakeProvider("irrelevant")

    with pytest.raises(InsufficientContextError):
        await generate_artifact(
            "markdown",
            "activation",
            [],
            provider,
        )


async def test_get_missing_artifact_returns_404(client):
    artifact_id = uuid.uuid4()

    response = await client.get(
        f"/api/artifacts/{artifact_id}"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ARTIFACT_NOT_FOUND"