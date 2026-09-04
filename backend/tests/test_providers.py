"""
Provider tests (section 26): Ollama, Anthropic, factory, invalid provider.

External calls are mocked — respx intercepts httpx (Ollama), and Anthropic's
client is monkeypatched — so this suite never touches a real Ollama server
or spends real API tokens.
"""
import httpx
import pytest
import respx

from app.exceptions import OllamaTimeoutError, OllamaUnavailableError, ProviderNotConfiguredError
from app.providers.base import ChatTurn
from app.providers.factory import available_providers, get_provider
from app.providers.ollama_provider import OllamaProvider


@respx.mock
async def test_ollama_generate_response_success():
    respx.post("http://fake-ollama:11434/api/chat").mock(
        return_value=httpx.Response(200, json={"message": {"content": "Focus on activation."}})
    )
    provider = OllamaProvider(base_url="http://fake-ollama:11434", model="llama3.2:3b")

    result = await provider.generate_response(
        system_prompt="You are helpful.", history=[ChatTurn(role="user", content="hi")]
    )
    assert result == "Focus on activation."


@respx.mock
async def test_ollama_generate_response_unavailable_raises_structured_error():
    respx.post("http://fake-ollama:11434/api/chat").mock(
        side_effect=httpx.ConnectError("connection refused")
    )
    provider = OllamaProvider(base_url="http://fake-ollama:11434", model="llama3.2:3b")

    with pytest.raises(OllamaUnavailableError):
        await provider.generate_response(
            system_prompt="You are helpful.", history=[ChatTurn(role="user", content="hi")]
        )


@respx.mock
async def test_ollama_generate_response_timeout_raises_structured_error():
    respx.post("http://fake-ollama:11434/api/chat").mock(side_effect=httpx.TimeoutException("slow"))
    provider = OllamaProvider(base_url="http://fake-ollama:11434", model="llama3.2:3b")

    with pytest.raises(OllamaTimeoutError):
        await provider.generate_response(
            system_prompt="You are helpful.", history=[ChatTurn(role="user", content="hi")]
        )


@respx.mock
async def test_ollama_stream_response_yields_chunks():
    body = (
        '{"message": {"content": "Focus "}, "done": false}\n'
        '{"message": {"content": "on activation."}, "done": true}\n'
    )
    respx.post("http://fake-ollama:11434/api/chat").mock(
        return_value=httpx.Response(200, content=body, headers={"content-type": "application/x-ndjson"})
    )
    provider = OllamaProvider(base_url="http://fake-ollama:11434", model="llama3.2:3b")

    chunks = []
    async for token in provider.stream_response(
        system_prompt="You are helpful.", history=[ChatTurn(role="user", content="hi")]
    ):
        chunks.append(token)

    assert "".join(chunks) == "Focus on activation."


@respx.mock
async def test_ollama_health_check_reports_down_when_unreachable():
    respx.get("http://fake-ollama:11434/api/tags").mock(side_effect=httpx.ConnectError("refused"))
    provider = OllamaProvider(base_url="http://fake-ollama:11434", model="llama3.2:3b")

    health = await provider.health_check()
    assert health.status == "down"


@respx.mock
async def test_ollama_health_check_flags_missing_model():
    respx.get("http://fake-ollama:11434/api/tags").mock(
        return_value=httpx.Response(200, json={"models": [{"name": "mistral:7b"}]})
    )
    provider = OllamaProvider(base_url="http://fake-ollama:11434", model="llama3.2:3b")

    health = await provider.health_check()
    assert health.status == "down"
    assert "llama3.2:3b" in health.detail


async def test_factory_returns_ollama_by_default(monkeypatch):
    monkeypatch.setattr("app.providers.factory.settings.default_llm_provider", "ollama")
    provider = get_provider(None)
    assert provider.name == "ollama"


async def test_factory_raises_when_anthropic_not_configured(monkeypatch):
    monkeypatch.setattr("app.providers.factory.settings.anthropic_api_key", None)
    with pytest.raises(ProviderNotConfiguredError):
        get_provider("anthropic")


async def test_factory_raises_for_unknown_provider():
    with pytest.raises(ProviderNotConfiguredError):
        get_provider("made-up-provider")


def test_available_providers_omits_anthropic_when_unconfigured(monkeypatch):
    monkeypatch.setattr("app.providers.factory.settings.anthropic_api_key", None)
    assert available_providers() == ["ollama"]


def test_available_providers_includes_anthropic_when_configured(monkeypatch):
    monkeypatch.setattr("app.providers.factory.settings.anthropic_api_key", "fake-key")
    assert available_providers() == ["ollama", "anthropic"]
