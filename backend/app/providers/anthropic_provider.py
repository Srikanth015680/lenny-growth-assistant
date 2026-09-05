from collections.abc import AsyncIterator

import anthropic

from app.exceptions import AnthropicUnavailableError
from app.providers.base import BaseLLMProvider, ChatTurn, ProviderHealth


class AnthropicProvider(BaseLLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model

    def _build_messages(self, history: list[ChatTurn]) -> list[dict]:
        return [
            {
                "role": turn.role,
                "content": turn.content,
            }
            for turn in history
        ]

    async def generate_response(
        self,
        *,
        system_prompt: str,
        history: list[ChatTurn],
    ) -> str:
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=self._build_messages(history),
            )

            return "".join(
                block.text
                for block in response.content
                if block.type == "text"
            )

        except anthropic.APIError as exc:
            raise AnthropicUnavailableError(
                "The Anthropic API is currently unavailable."
            ) from exc

    async def stream_response(
        self,
        *,
        system_prompt: str,
        history: list[ChatTurn],
    ) -> AsyncIterator[str]:
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=2048,
                system=system_prompt,
                messages=self._build_messages(history),
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except anthropic.APIError as exc:
            raise AnthropicUnavailableError(
                "The Anthropic API is currently unavailable."
            ) from exc

    async def health_check(self) -> ProviderHealth:
        try:
            await self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[
                    {
                        "role": "user",
                        "content": "ping",
                    }
                ],
            )

            return ProviderHealth(status="ok")

        except anthropic.APIError as exc:
            return ProviderHealth(
                status="down",
                detail=str(exc),
            )