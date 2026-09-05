import pytest

from app.exceptions import InsufficientContextError
from app.rag.retriever import RetrievedChunk
from app.skills.ship30_writer import write_ship30_essay


class FakeProvider:
    name = "fake"

    def __init__(self, reply: str):
        self.reply = reply
        self.received_system_prompt = None

    async def generate_response(self, *, system_prompt, history):
        self.received_system_prompt = system_prompt
        return self.reply

    async def stream_response(self, *, system_prompt, history):
        yield self.reply

    async def health_check(self):
        raise NotImplementedError


def make_chunk():
    return RetrievedChunk(
        episode="Ep 1",
        guest="Guest 1",
        timestamp="10:00",
        text="Activation matters.",
        score=0.9,
    )


async def test_ship30_requires_transcript_context():
    provider = FakeProvider("irrelevant")

    with pytest.raises(InsufficientContextError):
        await write_ship30_essay(
            "activation",
            chunks=[],
            provider=provider,
        )


async def test_ship30_uses_context_and_returns_essay():
    provider = FakeProvider(
        "## The Hook\n\nActivation is everything."
    )

    essay = await write_ship30_essay(
        "activation",
        chunks=[make_chunk()],
        provider=provider,
    )

    assert essay == "## The Hook\n\nActivation is everything."
    assert provider.received_system_prompt is not None
    assert "1,250 words" in provider.received_system_prompt
    assert "Ep 1" in provider.received_system_prompt