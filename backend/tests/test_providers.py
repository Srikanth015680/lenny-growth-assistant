import httpx
import pytest
import respx

from app.exceptions import (
    OllamaTimeoutError,
    OllamaUnavailableError,
    ProviderNotConfiguredError,
)
from app.providers.base import ChatTurn
from app.providers.factory import available_providers, get_provider
from app.providers.ollama_provider import OllamaProvider


OLLAMA_URL = "http://fake-ollama:11434"
MODEL = "llama3.2:3b"


def make_provider():
    return OllamaProvider(
        base_url=OLLAMA_URL,
        model=MODEL,
    )


@pytest.mark.asyncio
@respx.mock
async def test_ollama_generate_response():
    respx.post(f"{OLLAMA_URL}/api/chat").mock(
        return_value=httpx.Response(
            200,
            json={
                "message": {
                    "content": "Focus on activation.",
                }
            },
        )
    )

    provider = make_provider()

    result = await provider.generate_response(
        system_prompt="You are helpful.",
        history=[
            ChatTurn(role="user", content="hi"),
        ],
    )

    assert result == "Focus on activation."


@pytest.mark.asyncio
@respx.mock
async def test_ollama_connection_error():
    respx.post(f"{OLLAMA_URL}/api/chat").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    provider = make_provider()

    with pytest.raises(OllamaUnavailableError):
        await provider.generate_response(
            system_prompt="You are helpful.",
            history=[
                ChatTurn(role="user", content="hi"),
            ],
        )


@pytest.mark.asyncio
@respx.mock
async def test_ollama_timeout():
    respx.post(f"{OLLAMA_URL}/api/chat").mock(
        side_effect=httpx.TimeoutException("request timed out")
    )

    provider = make_provider()

    with pytest.raises(OllamaTimeoutError):
        await provider.generate_response(
            system_prompt="You are helpful.",
            history=[
                ChatTurn(role="user", content="hi"),
            ],
        )


@pytest.mark.asyncio
@respx.mock
async def test_ollama_stream_response():
    body = (
        '{"message":{"content":"Focus "},"done":false}\n'
        '{"message":{"content":"on activation."},"done":true}\n'
    )

    respx.post(f"{OLLAMA_URL}/api/chat").mock(
        return_value=httpx.Response(
            200,
            content=body,
            headers={"content-type": "application/x-ndjson"},
        )
    )

    provider = make_provider()

    chunks = []

    async for chunk in provider.stream_response(
        system_prompt="You are helpful.",
        history=[
            ChatTurn(role="user", content="hi"),
        ],
    ):
        chunks.append(chunk)

    assert "".join(chunks) == "Focus on activation."


@pytest.mark.asyncio
@respx.mock
async def test_ollama_health_check_when_unavailable():
    respx.get(f"{OLLAMA_URL}/api/tags").mock(
        side_effect=httpx.ConnectError("connection refused")
    )

    provider = make_provider()

    health = await provider.health_check()

    assert health.status == "down"


@pytest.mark.asyncio
@respx.mock
async def test_ollama_health_check_when_model_is_missing():
    respx.get(f"{OLLAMA_URL}/api/tags").mock(
        return_value=httpx.Response(
            200,
            json={
                "models": [
                    {"name": "mistral:7b"},
                ]
            },
        )
    )

    provider = make_provider()

    health = await provider.health_check()

    assert health.status == "down"
    assert MODEL in health.detail


def test_factory_uses_ollama_by_default(monkeypatch):
    monkeypatch.setattr(
        "app.providers.factory.settings.default_llm_provider",
        "ollama",
    )

    provider = get_provider(None)

    assert provider.name == "ollama"


def test_factory_rejects_unconfigured_anthropic(monkeypatch):
    monkeypatch.setattr(
        "app.providers.factory.settings.anthropic_api_key",
        None,
    )

    with pytest.raises(ProviderNotConfiguredError):
        get_provider("anthropic")


def test_factory_rejects_unknown_provider():
    with pytest.raises(ProviderNotConfiguredError):
        get_provider("made-up-provider")


def test_available_providers_without_anthropic(monkeypatch):
    monkeypatch.setattr(
        "app.providers.factory.settings.anthropic_api_key",
        None,
    )

    assert available_providers() == ["ollama"]


def test_available_providers_with_anthropic(monkeypatch):
    monkeypatch.setattr(
        "app.providers.factory.settings.anthropic_api_key",
        "fake-key",
    )

    assert available_providers() == ["ollama", "anthropic"]