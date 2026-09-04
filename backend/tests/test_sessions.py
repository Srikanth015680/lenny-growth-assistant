"""Section 26 "API" + "Persistence" test groups: session CRUD."""
import pytest


async def test_create_session_returns_defaults(client):
    resp = await client.post("/api/sessions", json={})
    assert resp.status_code == 201
    body = resp.json()
    assert body["title"] == "New conversation"
    assert "id" in body


async def test_create_session_with_title(client):
    resp = await client.post("/api/sessions", json={"title": "Activation ideas"})
    assert resp.status_code == 201
    assert resp.json()["title"] == "Activation ideas"


async def test_list_sessions(client):
    await client.post("/api/sessions", json={"title": "First"})
    await client.post("/api/sessions", json={"title": "Second"})

    resp = await client.get("/api/sessions")
    assert resp.status_code == 200
    titles = {s["title"] for s in resp.json()}
    assert {"First", "Second"}.issubset(titles)


async def test_get_session_detail_includes_empty_messages(client):
    created = (await client.post("/api/sessions", json={"title": "Detail test"})).json()

    resp = await client.get(f"/api/sessions/{created['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == created["id"]
    assert body["messages"] == []


async def test_get_nonexistent_session_returns_structured_404(client):
    resp = await client.get("/api/sessions/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "SESSION_NOT_FOUND"
