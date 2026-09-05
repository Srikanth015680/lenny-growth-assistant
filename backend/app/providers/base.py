from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class ChatTurn:
    role: str
    content: str


@dataclass
class ProviderHealth:
    status: str
    detail: str | None = None


class BaseLLMProvider(ABC):
    name: str

    @abstractmethod
    async def generate_response(
        self,
        *,
        system_prompt: str,
        history: list[ChatTurn],
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def stream_response(
        self,
        *,
        system_prompt: str,
        history: list[ChatTurn],
    ) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def health_check(self) -> ProviderHealth:
        raise NotImplementedError