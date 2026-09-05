from app.models.schemas import ChatMode


def infer_mode_from_text(message: str) -> ChatMode | None:
    """
    Reserved for future intent classification.

    Free-text routing should be added here later instead of scattering
    keyword checks throughout the application.
    """
    return None


def resolve_mode(explicit_mode: ChatMode, message: str) -> ChatMode:
    """
    Resolve the mode used by the agent.

    Explicit non-default modes always win. For the default mode, we leave
    room for future text-based intent classification.
    """
    if explicit_mode != ChatMode.DEFAULT:
        return explicit_mode

    inferred_mode = infer_mode_from_text(message)

    return inferred_mode or ChatMode.DEFAULT