from app.models.db_models import Message
from app.providers.base import ChatTurn


MAX_HISTORY_TURNS = 20


def build_history(messages: list[Message]) -> list[ChatTurn]:
    messages = [
        message
        for message in messages
        if message.role in {"user", "assistant"}
    ]

    messages = messages[-MAX_HISTORY_TURNS:]

    return [
        ChatTurn(
            role=message.role,
            content=message.content,
        )
        for message in messages
    ]