"""
Ship30 skill tests (section 26): now implemented — grounded generation via
a mocked provider, and the insufficient-context refusal when nothing was
retrieved.
"""
import pytest

from app.exceptions import InsufficientContextError
from app.rag.retriever import RetrievedChunk
from app.skills.ship30_writer import write_ship30_essay


class _FakeProvider:
    name = "fake"

    def __init__(self, reply: str):
        self.reply = reply
        self.received_system_prompt: str | None = None

    async def generate_response(self, *, system_prompt, history):
        self.received_system_prompt = system_prompt
        return self.reply

    async def stream_response(self, *, system_prompt, history):
        yield self.reply

    async def health_check(self):
        raise NotImplementedError


async def test_write_ship30_essay_raises_when_no_context():
    with pytest.raises(InsufficientContextError):
        await write_ship30_essay("activation", chunks=[], provider=_FakeProvider("irrelevant"))


async def test_write_ship30_essay_returns_provider_output_and_grounds_prompt():
    chunk = RetrievedChunk(
        episode="Ep 1", guest="Guest 1", timestamp="10:00", text="Activation matters.", score=0.9
    )
    provider = _FakeProvider("## The Hook\n\nActivation is everything.")

    essay = await write_ship30_essay("activation", chunks=[chunk], provider=provider)

    assert essay == "## The Hook\n\nActivation is everything."
    assert "1,250 words" in provider.received_system_prompt
    assert "Ep 1" in provider.received_system_prompt
