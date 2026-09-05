import json
from collections.abc import AsyncIterator

import httpx

from app.exceptions import OllamaTimeoutError, OllamaUnavailableError
from app.logging_config import get_logger
from app.providers.base import BaseLLMProvider, ChatTurn, ProviderHealth

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: int = 60,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _build_messages(
        self,
        system_prompt: str,
        history: list[ChatTurn],
    ) -> list[dict]:
        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        for turn in history:
            messages.append(
                {
                    "role": turn.role,
                    "content": turn.content,
                }
            )

        return messages

    async def generate_response(
        self,
        *,
        system_prompt: str,
        history: list[ChatTurn],
    ) -> str:
        payload = {
            "model": self.model,
            "messages": self._build_messages(system_prompt, history),
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds
            ) as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                )

                response.raise_for_status()

                data = response.json()

                return data.get("message", {}).get("content", "")

        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(
                f"Ollama did not respond within {self.timeout_seconds} seconds."
            ) from exc

        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(
                "Ollama is unavailable. Make sure Ollama is running "
                "or select another provider."
            ) from exc

    async def stream_response(
        self,
        *,
        system_prompt: str,
        history: list[ChatTurn],
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": self._build_messages(system_prompt, history),
            "stream": True,
        }

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout_seconds
            ) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                ) as response:

                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue

                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning(
                                "Invalid response received from Ollama"
                            )
                            continue

                        content = data.get("message", {}).get(
                            "content", ""
                        )

                        if content:
                            yield content

                        if data.get("done"):
                            break

        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(
                f"Ollama did not respond within {self.timeout_seconds} seconds."
            ) from exc

        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(
                "Ollama is unavailable. Make sure Ollama is running "
                "or select another provider."
            ) from exc

    async def health_check(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(
                    f"{self.base_url}/api/tags"
                )

                response.raise_for_status()

                data = response.json()

                models = [
                    model.get("name")
                    for model in data.get("models", [])
                ]

                if self.model not in models:
                    return ProviderHealth(
                        status="down",
                        detail=(
                            f"Model '{self.model}' is not installed. "
                            f"Run: ollama pull {self.model}"
                        ),
                    )

                return ProviderHealth(status="ok")

        except httpx.TimeoutException:
            return ProviderHealth(
                status="down",
                detail="Ollama health check timed out.",
            )

        except httpx.HTTPError as exc:
            return ProviderHealth(
                status="down",
                detail=str(exc),
            )