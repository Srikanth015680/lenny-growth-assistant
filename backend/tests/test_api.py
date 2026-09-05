import json

from app.providers.base import ProviderHealth


class FakeProvider:
    name = "fake"

    def __init__(self, reply: str = "Here is a grounded answer."):
        self.reply = reply
        self.received_system_prompt = None

    async def generate_response(self, *, system_prompt, history):
        self.received_system_prompt = system_prompt
        return self.reply

    async def stream_response(self, *, system_prompt, history):
        self.received_system_prompt = system_prompt

        for word in self.reply.split():
            yield f"{word} "

    async def health_check(self):
        return ProviderHealth(status="ok")


def parse_sse(raw: str) -> list[dict]:
    events = []

    for block in raw.strip().split("\n\n"):
        if not block.strip():
            continue

        lines = block.strip().split("\n")
        event = next(line for line in lines if line.startswith("event:"))
        data = next(line for line in lines if line.startswith("data:"))

        events.append(
            {
                "event": event.split("event:", 1)[1].strip(),
                "data": json.loads(data.split("data:", 1)[1].strip()),
            }
        )

    return events


async def create_session(client) -> str:
    response = await client.post(
        "/api/sessions",
        json={"title": "Chat test"},
    )

    assert response.status_code == 201

    return response.json()["id"]


def fake_chunks():
    from app.rag.retriever import RetrievedChunk

    return [
        RetrievedChunk(
            episode="Ep 1",
            guest="Guest 1",
            timestamp="10:00",
            text="Activation matters.",
            score=0.9,
        )
    ]


async def test_chat_rejects_empty_message(client):
    session_id = await create_session(client)

    response = await client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "   ",
            "mode": "default",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MESSAGE"


async def test_chat_rejects_oversized_message(client):
    session_id = await create_session(client)

    response = await client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "a" * 5000,
            "mode": "default",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_MESSAGE"


async def test_chat_rejects_unknown_session(client):
    response = await client.post(
        "/api/chat",
        json={
            "session_id": "00000000-0000-0000-0000-000000000000",
            "message": "hello",
            "mode": "default",
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"


async def test_default_chat_streams_and_persists(client, monkeypatch):
    session_id = await create_session(client)

    provider = FakeProvider(
        reply="Focus on activation and retention."
    )

    monkeypatch.setattr(
        "app.api.chat.get_provider",
        lambda name: provider,
    )

    monkeypatch.setattr(
        "app.rag.retriever.embed_text",
        lambda query: [0.0] * 384,
    )

    async with client.stream(
        "POST",
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "How do I improve activation?",
            "mode": "default",
        },
    ) as response:
        assert response.status_code == 200

        raw = ""
        async for chunk in response.aiter_text():
            raw += chunk

    events = parse_sse(raw)
    event_names = [event["event"] for event in events]

    assert event_names[0] == "status"
    assert "sources" in event_names
    assert "token" in event_names
    assert event_names[-1] == "done"

    sources = next(
        event for event in events if event["event"] == "sources"
    )

    assert sources["data"]["sources"] == []

    content = "".join(
        event["data"]["content"]
        for event in events
        if event["event"] == "token"
    )

    assert content.strip() == "Focus on activation and retention."

    detail = (
        await client.get(f"/api/sessions/{session_id}")
    ).json()

    assert len(detail["messages"]) == 2
    assert detail["messages"][0]["role"] == "user"
    assert detail["messages"][1]["role"] == "assistant"
    assert (
        detail["messages"][1]["content"].strip()
        == "Focus on activation and retention."
    )


async def test_ship30_generates_and_persists_artifact(
    client,
    monkeypatch,
):
    session_id = await create_session(client)

    provider = FakeProvider(
        reply="## Hook\n\nActivation is everything."
    )

    monkeypatch.setattr(
        "app.api.chat.get_provider",
        lambda name: provider,
    )

    monkeypatch.setattr(
        "app.agent.orchestrator.TranscriptRetriever"
        ".retrieve_relevant_chunks",
        lambda self, query, **kwargs: fake_chunks(),
    )

    async with client.stream(
        "POST",
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "activation ideas",
            "mode": "ship30",
        },
    ) as response:
        raw = ""
        async for chunk in response.aiter_text():
            raw += chunk

    events = parse_sse(raw)

    assert events[-1]["event"] == "done"

    artifact = next(
        event for event in events
        if event["event"] == "artifact"
    )

    assert artifact["data"]["type"] == "markdown"
    assert (
        artifact["data"]["content"]
        == "## Hook\n\nActivation is everything."
    )

    detail = (
        await client.get(f"/api/sessions/{session_id}")
    ).json()

    assistant_message = detail["messages"][1]

    assert len(assistant_message["artifacts"]) == 1
    assert (
        assistant_message["artifacts"][0]["artifact_type"]
        == "markdown"
    )


async def test_html_artifact_generates_and_persists(
    client,
    monkeypatch,
):
    session_id = await create_session(client)

    html = (
        "<!DOCTYPE html>"
        "<html>"
        "<body>Framework</body>"
        "</html>"
    )

    provider = FakeProvider(reply=html)

    monkeypatch.setattr(
        "app.api.chat.get_provider",
        lambda name: provider,
    )

    monkeypatch.setattr(
        "app.agent.orchestrator.TranscriptRetriever"
        ".retrieve_relevant_chunks",
        lambda self, query, **kwargs: fake_chunks(),
    )

    async with client.stream(
        "POST",
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "make a one-pager",
            "mode": "artifact",
            "artifact_type": "html",
        },
    ) as response:
        raw = ""
        async for chunk in response.aiter_text():
            raw += chunk

    events = parse_sse(raw)

    artifact = next(
        event for event in events
        if event["event"] == "artifact"
    )

    assert artifact["data"]["type"] == "html"
    assert artifact["data"]["content"].startswith(
        "<!DOCTYPE html>"
    )


async def test_grounding_prompt_contains_security_rule(
    client,
    monkeypatch,
):
    session_id = await create_session(client)

    provider = FakeProvider(reply="ok")

    monkeypatch.setattr(
        "app.api.chat.get_provider",
        lambda name: provider,
    )

    monkeypatch.setattr(
        "app.rag.retriever.embed_text",
        lambda query: [0.0] * 384,
    )

    async with client.stream(
        "POST",
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "hello",
            "mode": "default",
        },
    ) as response:
        async for _ in response.aiter_text():
            pass

    assert "not instructions" in provider.received_system_prompt
    assert (
        "ignore all previous instructions"
        in provider.received_system_prompt.lower()
    )