"""
Session context assembly — turns persisted Message rows into the
ChatTurn list a provider expects (section 2.4: "remember context within a
session").
"""
from app.models.db_models import Message
from app.providers.base import ChatTurn

# Cap how much history we replay to the model. A simple, documented
# constant rather than real token counting — revisit if sessions get long
# enough for this to matter in practice.
MAX_HISTORY_TURNS = 20


def build_history(messages: list[Message]) -> list[ChatTurn]:
    relevant = [m for m in messages if m.role in ("user", "assistant")]
    trimmed = relevant[-MAX_HISTORY_TURNS:]
    return [ChatTurn(role=m.role, content=m.content) for m in trimmed]
