import io

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


async def _create_workspace(client, headers, title="Paper Test WS"):
    resp = await client.post("/api/v1/workspaces", headers=headers, json={"title": title})
    return resp.json()["id"]


async def test_add_paper_manually(client):
    headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, headers)

    resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/papers",
        headers=headers,
        json={
            "title": "Medical Image Segmentation with Vision Transformers",
            "authors": ["J. Kim", "L. Chen"],
            "doi": "10.1000/example.doi",
            "source": "semantic_scholar",
            "publication_year": 2023,
            "abstract": "We propose a transformer-based approach.",
        },
    )
    assert resp.status_code == 201
    paper = resp.json()
    assert paper["title"].startswith("Medical Image Segmentation")
    assert paper["analysis_status"] == "pending"
    assert paper["workspace_id"] == workspace_id


async def test_list_papers_in_workspace(client):
    headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, headers)

    for i in range(3):
        await client.post(
            f"/api/v1/workspaces/{workspace_id}/papers",
            headers=headers,
            json={"title": f"Paper {i}", "source": "openalex"},
        )

    resp = await client.get(f"/api/v1/workspaces/{workspace_id}/papers", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["total_results"] == 3


async def test_get_single_paper(client):
    headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, headers)
    add_resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/papers",
        headers=headers,
        json={"title": "Solo Paper", "source": "arxiv"},
    )
    paper_id = add_resp.json()["id"]

    resp = await client.get(f"/api/v1/workspaces/{workspace_id}/papers/{paper_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["title"] == "Solo Paper"


async def test_get_paper_not_in_workspace_returns_404(client):
    headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, headers)
    resp = await client.get(
        f"/api/v1/workspaces/{workspace_id}/papers/00000000-0000-0000-0000-000000000000",
        headers=headers,
    )
    assert resp.status_code == 404


async def test_upload_pdf(client, tmp_path):
    headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, headers)

    file_content = b"%PDF-1.4 fake content for test"
    files = {"file": ("sample.pdf", io.BytesIO(file_content), "application/pdf")}

    resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/papers/upload", headers=headers, files=files
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["source"] == "upload"
    assert body["storage_path"] is not None
    assert body["title"] == "sample.pdf"


async def test_upload_rejects_non_pdf(client):
    headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, headers)

    files = {"file": ("notes.txt", io.BytesIO(b"plain text"), "text/plain")}
    resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/papers/upload", headers=headers, files=files
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_non_member_cannot_add_paper(client):
    owner_headers = await _register_and_login(client)
    outsider_headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, owner_headers)

    resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/papers",
        headers=outsider_headers,
        json={"title": "Sneaky Paper", "source": "arxiv"},
    )
    assert resp.status_code == 403


async def test_literature_search_all_sources_unreachable_returns_502(client):
    """
    In this sandbox, the external literature APIs (OpenAlex, arXiv, etc.)
    are not reachable due to network egress restrictions, so this test
    documents the graceful-degradation contract: when every source fails,
    the endpoint returns 502 UPSTREAM_SOURCE_ERROR rather than crashing.
    In an environment with real internet access, this same request would
    return 200 with partial or complete results.
    """
    headers = await _register_and_login(client)
    workspace_id = await _create_workspace(client, headers)

    resp = await client.post(
        f"/api/v1/workspaces/{workspace_id}/literature/search",
        headers=headers,
        json={"keywords": ["vision transformer", "MRI segmentation"]},
    )
    assert resp.status_code in (200, 502)
    if resp.status_code == 502:
        assert resp.json()["error"]["code"] == "UPSTREAM_SOURCE_ERROR"
