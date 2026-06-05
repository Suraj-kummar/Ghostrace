"""Tests for session list, get, delete, and search endpoints."""
from __future__ import annotations
import pytest


SIGNUP_PAYLOAD = {
    "email": "session_test@example.com",
    "password": "SecurePass1!",
}


async def _get_token(client) -> str:
    await client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/api/auth/token",
        data={"username": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    return resp.json()["access_token"]


async def _get_project_id(client, token: str) -> str:
    resp = await client.get("/api/projects/", headers={"Authorization": f"Bearer {token}"})
    return resp.json()[0]["id"]


@pytest.mark.asyncio
async def test_list_sessions_empty(client):
    token = await _get_token(client)
    project_id = await _get_project_id(client, token)
    resp = await client.get(
        "/api/sessions/",
        params={"project_id": project_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_list_sessions_pagination(client):
    token = await _get_token(client)
    project_id = await _get_project_id(client, token)
    resp = await client.get(
        "/api/sessions/",
        params={"project_id": project_id, "skip": 0, "limit": 10},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_session_not_found(client):
    token = await _get_token(client)
    resp = await client.get(
        "/api/sessions/nonexistent-session-id",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions_wrong_project(client):
    token = await _get_token(client)
    resp = await client.get(
        "/api/sessions/",
        params={"project_id": "nonexistent-project"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_session_not_found(client):
    token = await _get_token(client)
    resp = await client.delete(
        "/api/sessions/nonexistent-session",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_session_not_found(client):
    token = await _get_token(client)
    resp = await client.get(
        "/api/sessions/nonexistent-session/export",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_sessions_requires_auth(client):
    resp = await client.get("/api/sessions/", params={"project_id": "any"})
    assert resp.status_code == 401
