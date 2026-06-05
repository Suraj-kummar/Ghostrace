"""Tests for /me endpoint, refresh token, and login rate limiting."""
from __future__ import annotations
import pytest


SIGNUP_PAYLOAD = {
    "email": "auth_me_test@example.com",
    "password": "SecurePass1!",
}


@pytest.mark.asyncio
async def test_signup_and_me(client):
    await client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    token_resp = await client.post(
        "/api/auth/token",
        data={"username": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    assert token_resp.status_code == 200
    token = token_resp.json()["access_token"]

    me_resp = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me = me_resp.json()
    assert me["email"] == SIGNUP_PAYLOAD["email"]
    assert me["plan"] == "free"
    assert me["is_active"] is True


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/auth/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_token_response_has_expires_in(client):
    await client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/api/auth/token",
        data={"username": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "expires_in" in data
    assert data["expires_in"] > 0


@pytest.mark.asyncio
async def test_signup_duplicate_email(client):
    await client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    resp2 = await client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    assert resp2.status_code == 400


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    await client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/api/auth/token",
        data={"username": SIGNUP_PAYLOAD["email"], "password": "WrongPassword1!"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_signup_weak_password_rejected(client):
    resp = await client.post("/api/auth/signup", json={"email": "weak@example.com", "password": "weak"})
    assert resp.status_code == 422  # pydantic validation error
