"""
Ollama provider — the default, local inference backend (section 12).

Must never crash the API when Ollama is unavailable, the model is missing,
or the request times out; callers get a structured AppError instead
(handled centrally in app/exceptions.py) and the rest of the app keeps
running.
"""
import json
from collections.abc import AsyncIterator

import httpx

from app.exceptions import OllamaTimeoutError, OllamaUnavailableError
from app.logging_config import get_logger
from app.providers.base import BaseLLMProvider, ChatTurn, ProviderHealth

logger = get_logger(__name__)


class OllamaProvider(BaseLLMProvider):
    name = "ollama"

    def __init__(self, base_url: str, model: str, timeout_seconds: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def _messages_payload(
        self, system_prompt: str, history: list[ChatTurn]
    ) -> list[dict]:
        messages = [{"role": "system", "content": system_prompt}]
        messages += [{"role": h.role, "content": h.content} for h in history]
        return messages

    async def generate_response(
        self, *, system_prompt: str, history: list[ChatTurn]
    ) -> str:
        payload = {
            "model": self.model,
            "messages": self._messages_payload(system_prompt, history),
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.post(f"{self.base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("message", {}).get("content", "")
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(
                f"Ollama did not respond within {self.timeout_seconds}s."
            ) from exc
        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(
                "Local Ollama is unavailable. Start Ollama or select another provider."
            ) from exc

    async def stream_response(
        self, *, system_prompt: str, history: list[ChatTurn]
    ) -> AsyncIterator[str]:
        payload = {
            "model": self.model,
            "messages": self._messages_payload(system_prompt, history),
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                async with client.stream(
                    "POST", f"{self.base_url}/api/chat", json=payload
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                        except json.JSONDecodeError:
                            logger.warning("ollama_malformed_chunk", extra={"line": line[:200]})
                            continue
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                        if chunk.get("done"):
                            break
        except httpx.TimeoutException as exc:
            raise OllamaTimeoutError(
                f"Ollama did not respond within {self.timeout_seconds}s."
            ) from exc
        except httpx.HTTPError as exc:
            raise OllamaUnavailableError(
                "Local Ollama is unavailable. Start Ollama or select another provider."
            ) from exc

    async def health_check(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
                if self.model not in models:
                    return ProviderHealth(
                        status="down",
                        detail=f"Model '{self.model}' is not pulled. Run: ollama pull {self.model}",
                    )
                return ProviderHealth(status="ok")
        except httpx.HTTPError as exc:
            return ProviderHealth(status="down", detail=str(exc))
