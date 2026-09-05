from app.agent.router import resolve_mode


def test_resolve_mode_uses_default_mode():
    result = resolve_mode(
        "default",
        "How do I improve activation?",
    )

    assert result == "default"


def test_resolve_mode_uses_ship30_mode():
    result = resolve_mode(
        "ship30",
        "Turn that into a Ship 30 essay",
    )

    assert result == "ship30"


def test_resolve_mode_uses_artifact_mode():
    result = resolve_mode(
        "artifact",
        "Create a one-page HTML framework",
    )

    assert result == "artifact"


def test_resolve_mode_does_not_infer_mode_from_message():
    result = resolve_mode(
        "default",
        "Turn that into a Ship 30 essay",
    )

    assert result == "default"