"""
ProviderFactory — the single place that decides which BaseLLMProvider
implementation to hand back (section 11).

Callers ask for "ollama" or "anthropic" (or None, meaning "use the
configured default"); they never import a concrete provider class
directly.
"""
from app.config import settings
from app.exceptions import ProviderNotConfiguredError
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import BaseLLMProvider
from app.providers.ollama_provider import OllamaProvider

_ollama_singleton: OllamaProvider | None = None
_anthropic_singleton: AnthropicProvider | None = None


def get_provider(name: str | None = None) -> BaseLLMProvider:
    global _ollama_singleton, _anthropic_singleton

    resolved = name or settings.default_llm_provider

    if resolved == "ollama":
        if _ollama_singleton is None:
            _ollama_singleton = OllamaProvider(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                timeout_seconds=settings.ollama_timeout_seconds,
            )
        return _ollama_singleton

    if resolved == "anthropic":
        if not settings.anthropic_available:
            raise ProviderNotConfiguredError(
                "Anthropic is not configured (no ANTHROPIC_API_KEY set). "
                "Use the Ollama provider instead."
            )
        if _anthropic_singleton is None:
            _anthropic_singleton = AnthropicProvider(
                api_key=settings.anthropic_api_key,  # type: ignore[arg-type]
                model=settings.anthropic_model,
            )
        return _anthropic_singleton

    raise ProviderNotConfiguredError(f"Unknown provider '{resolved}'.")


def available_providers() -> list[str]:
    providers = ["ollama"]
    if settings.anthropic_available:
        providers.append("anthropic")
    return providers
