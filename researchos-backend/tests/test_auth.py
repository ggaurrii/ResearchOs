import pytest

from tests.conftest import unique_email

pytestmark = pytest.mark.asyncio


async def _register(client, email, password="P@ssw0rd123", role="student"):
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test User", "role": role},
    )


async def test_register_success(client):
    email = unique_email()
    resp = await _register(client, email)
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == email
    assert body["role"] == "student"
    assert body["status"] == "active"
    assert "password" not in body
    assert "password_hash" not in body


async def test_register_duplicate_email_returns_409(client):
    email = unique_email()
    first = await _register(client, email)
    assert first.status_code == 201

    second = await _register(client, email)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED" or second.json()["error"]["code"] == "CONFLICT"


async def test_register_weak_password_rejected(client):
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email(), "password": "allletters", "full_name": "Test", "role": "student"},
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_login_success_and_me(client):
    email = unique_email()
    await _register(client, email)

    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "P@ssw0rd123"})
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens and "refresh_token" in tokens

    me = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == email


async def test_login_wrong_password(client):
    email = unique_email()
    await _register(client, email)
    resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrongpass1"})
    assert resp.status_code == 401


async def test_account_locks_after_max_failed_attempts(client):
    email = unique_email()
    await _register(client, email)

    for _ in range(5):
        resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "wrongpass1"})
        assert resp.status_code == 401

    # 6th attempt, even with the correct password, should now be locked.
    locked_resp = await client.post("/api/v1/auth/login", json={"email": email, "password": "P@ssw0rd123"})
    assert locked_resp.status_code == 401
    assert "locked" in locked_resp.json()["error"]["message"].lower()


async def test_me_requires_token(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


async def test_refresh_token_rotation(client):
    email = unique_email()
    await _register(client, email)
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": "P@ssw0rd123"})
    old_refresh = login.json()["refresh_token"]

    refreshed = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert refreshed.status_code == 200
    # The refresh token is always freshly randomly generated; the access
    # token could legitimately be byte-identical if issued within the same
    # second (identical iat/exp/sub/role payload), so we assert on the part
    # of the response that's guaranteed to differ.
    assert refreshed.json()["refresh_token"] != old_refresh

    # The old refresh token must now be revoked (single use / rotation).
    reused = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reused.status_code == 401
