import pytest

from tests.conftest import unique_email

pytestmark = pytest.mark.asyncio


async def _register_and_login(client, role="researcher"):
    email = unique_email()
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "P@ssw0rd123", "full_name": "Test User", "role": role},
    )
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "P@ssw0rd123"})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_create_and_get_workspace(client):
    headers = await _register_and_login(client)
    create_resp = await client.post(
        "/api/v1/workspaces",
        headers=headers,
        json={"title": "ViT for MRI Segmentation", "domain": "Medical Imaging", "visibility": "private"},
    )
    assert create_resp.status_code == 201
    workspace = create_resp.json()
    assert workspace["title"] == "ViT for MRI Segmentation"
    assert workspace["visibility"] == "private"
    assert workspace["status"] == "active"

    get_resp = await client.get(f"/api/v1/workspaces/{workspace['id']}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == workspace["id"]


async def test_list_my_workspaces(client):
    headers = await _register_and_login(client)
    await client.post("/api/v1/workspaces", headers=headers, json={"title": "WS1"})
    await client.post("/api/v1/workspaces", headers=headers, json={"title": "WS2"})

    listing = await client.get("/api/v1/workspaces", headers=headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total_results"] == 2
    assert len(body["results"]) == 2


async def test_non_member_cannot_view_private_workspace(client):
    owner_headers = await _register_and_login(client)
    outsider_headers = await _register_and_login(client)

    create_resp = await client.post("/api/v1/workspaces", headers=owner_headers, json={"title": "Private WS"})
    workspace_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/workspaces/{workspace_id}", headers=outsider_headers)
    assert resp.status_code == 403


async def test_public_workspace_is_readable_by_non_member(client):
    owner_headers = await _register_and_login(client)
    outsider_headers = await _register_and_login(client)

    create_resp = await client.post(
        "/api/v1/workspaces", headers=owner_headers, json={"title": "Public WS", "visibility": "public"}
    )
    workspace_id = create_resp.json()["id"]

    resp = await client.get(f"/api/v1/workspaces/{workspace_id}", headers=outsider_headers)
    assert resp.status_code == 200


async def test_only_owner_can_update_workspace(client):
    owner_headers = await _register_and_login(client)
    outsider_headers = await _register_and_login(client)

    create_resp = await client.post("/api/v1/workspaces", headers=owner_headers, json={"title": "Owned WS"})
    workspace_id = create_resp.json()["id"]

    forbidden = await client.patch(
        f"/api/v1/workspaces/{workspace_id}", headers=outsider_headers, json={"title": "Hijacked"}
    )
    assert forbidden.status_code == 403

    allowed = await client.patch(
        f"/api/v1/workspaces/{workspace_id}", headers=owner_headers, json={"title": "Renamed"}
    )
    assert allowed.status_code == 200
    assert allowed.json()["title"] == "Renamed"


async def test_workspace_creation_logs_activity(client):
    headers = await _register_and_login(client)
    create_resp = await client.post("/api/v1/workspaces", headers=headers, json={"title": "Logged WS"})
    workspace_id = create_resp.json()["id"]

    activity = await client.get(f"/api/v1/workspaces/{workspace_id}/activity", headers=headers)
    assert activity.status_code == 200
    events = [e["event_type"] for e in activity.json()["results"]]
    assert "workspace_created" in events


async def test_get_nonexistent_workspace_returns_404(client):
    headers = await _register_and_login(client)
    resp = await client.get(
        "/api/v1/workspaces/00000000-0000-0000-0000-000000000000", headers=headers
    )
    assert resp.status_code == 404
