async def test_create_session_uses_default_title(client):
    response = await client.post("/api/sessions", json={})

    assert response.status_code == 201

    data = response.json()

    assert data["title"] == "New conversation"
    assert "id" in data


async def test_create_session_with_custom_title(client):
    response = await client.post(
        "/api/sessions",
        json={"title": "Activation ideas"},
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Activation ideas"


async def test_list_sessions(client):
    await client.post(
        "/api/sessions",
        json={"title": "First"},
    )
    await client.post(
        "/api/sessions",
        json={"title": "Second"},
    )

    response = await client.get("/api/sessions")

    assert response.status_code == 200

    titles = {session["title"] for session in response.json()}

    assert {"First", "Second"}.issubset(titles)


async def test_get_session_returns_empty_messages(client):
    created = (
        await client.post(
            "/api/sessions",
            json={"title": "Detail test"},
        )
    ).json()

    response = await client.get(
        f"/api/sessions/{created['id']}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == created["id"]
    assert data["messages"] == []


async def test_get_missing_session_returns_404(client):
    session_id = "00000000-0000-0000-0000-000000000000"

    response = await client.get(
        f"/api/sessions/{session_id}"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SESSION_NOT_FOUND"