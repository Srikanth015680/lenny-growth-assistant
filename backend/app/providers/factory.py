from app.config import settings
from app.exceptions import ProviderNotConfiguredError
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import BaseLLMProvider
from app.providers.ollama_provider import OllamaProvider


_ollama_provider: OllamaProvider | None = None
_anthropic_provider: AnthropicProvider | None = None


def get_provider(name: str | None = None) -> BaseLLMProvider:
    global _ollama_provider, _anthropic_provider

    provider_name = name or settings.default_llm_provider

    if provider_name == "ollama":
        if _ollama_provider is None:
            _ollama_provider = OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                timeout_seconds=settings.ollama_timeout_seconds,
            )

        return _ollama_provider

    if provider_name == "anthropic":
        if not settings.anthropic_available:
            raise ProviderNotConfiguredError(
                "Anthropic is not configured. "
                "Set ANTHROPIC_API_KEY or use Ollama."
            )

        if _anthropic_provider is None:
            _anthropic_provider = AnthropicProvider(
                api_key=settings.anthropic_api_key,
                model=settings.anthropic_model,
            )

        return _anthropic_provider

    raise ProviderNotConfiguredError(
        f"Unknown provider: {provider_name}"
    )


def available_providers() -> list[str]:
    providers = ["ollama"]

    if settings.anthropic_available:
        providers.append("anthropic")

    return providers