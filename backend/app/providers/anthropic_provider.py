"""
Anthropic provider — optional cloud backend (section 13).

The API key is read once from settings (never hard-coded, never logged).
If it's absent, ProviderFactory simply won't construct this provider — see
factory.py — so the rest of the app keeps working on Ollama alone.
"""
from collections.abc import AsyncIterator

import anthropic

from app.exceptions import AnthropicUnavailableError
from app.providers.base import BaseLLMProvider, ChatTurn, ProviderHealth


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    def _messages_payload(self, history: list[ChatTurn]) -> list[dict]:
        # Anthropic's Messages API takes system separately, so history here
        # excludes it (unlike OllamaProvider, which folds it into `messages`).
        return [{"role": h.role, "content": h.content} for h in history]

    async def generate_response(
        self, *, system_prompt: str, history: list[ChatTurn]
    ) -> str:
        try:
            resp = await self._client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=self._messages_payload(history),
            )
            return "".join(block.text for block in resp.content if block.type == "text")
        except anthropic.APIError as exc:
            raise AnthropicUnavailableError(
                "The Anthropic API is currently unavailable."
            ) from exc

    async def stream_response(
        self, *, system_prompt: str, history: list[ChatTurn]
    ) -> AsyncIterator[str]:
        try:
            async with self._client.messages.stream(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=self._messages_payload(history),
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except anthropic.APIError as exc:
            raise AnthropicUnavailableError(
                "The Anthropic API is currently unavailable."
            ) from exc

    async def health_check(self) -> ProviderHealth:
        try:
            # A cheap call that exercises auth without spending many tokens.
            await self._client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "ping"}],
            )
            return ProviderHealth(status="ok")
        except anthropic.APIError as exc:
            return ProviderHealth(status="down", detail=str(exc))
