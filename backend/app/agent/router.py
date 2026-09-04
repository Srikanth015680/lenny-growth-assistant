"""
Agent routing (section 14).

Routing decisions are driven primarily by the explicit `mode` field the
frontend sends (default | ship30 | artifact) — e.g. the user clicked a
"Turn into Ship 30 essay" action. That's a deliberate choice, not "fragile
keyword matching": mode is a structured, versioned enum on the request
contract (schemas.ChatMode), so it can be extended by adding new skills
without touching string-matching heuristics anywhere.

A future phase can additionally infer mode from free-text follow-ups
("Turn that into a Ship 30 essay" typed into the default chat box) by
running a small classification step here before falling through to the
explicit mode — that hook is `infer_mode_from_text`, currently a
placeholder so the seam is visible in the code without pretending it's
implemented.
"""
from app.models.schemas import ChatMode


def infer_mode_from_text(message: str) -> ChatMode | None:
    """Placeholder for future free-text intent classification (section 14's
    "Turn that into a Ship 30 essay" example). Not implemented in this
    phase — returns None so callers fall back to the explicit mode field."""
    return None


def resolve_mode(explicit_mode: ChatMode, message: str) -> ChatMode:
    if explicit_mode != "default":
        return explicit_mode
    inferred = infer_mode_from_text(message)
    return inferred or explicit_mode
