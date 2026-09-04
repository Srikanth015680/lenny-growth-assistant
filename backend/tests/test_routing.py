"""Agent routing tests (section 26): normal question, ship30 request, artifact
request. See app/agent/router.py for why this isn't keyword-matching."""
from app.agent.router import resolve_mode


def test_resolve_mode_passes_through_explicit_default():
    assert resolve_mode("default", "How do I improve activation?") == "default"


def test_resolve_mode_passes_through_explicit_ship30():
    assert resolve_mode("ship30", "Turn that into a Ship 30 essay") == "ship30"


def test_resolve_mode_passes_through_explicit_artifact():
    assert resolve_mode("artifact", "Create a one-page HTML framework") == "artifact"


def test_resolve_mode_defaults_stay_default_until_text_inference_lands():
    # infer_mode_from_text is an intentional placeholder (see router.py) —
    # this pins current behavior so the switch to real inference later is
    # a deliberate, visible change to this test, not a silent regression.
    assert resolve_mode("default", "Turn that into a Ship 30 essay") == "default"
