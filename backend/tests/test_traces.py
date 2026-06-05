"""Tests for trace event analytics endpoints."""
from __future__ import annotations
import pytest


SIGNUP_PAYLOAD = {
    "email": "trace_test@example.com",
    "password": "SecurePass1!",
}


async def _get_auth(client):
    await client.post("/api/auth/signup", json=SIGNUP_PAYLOAD)
    resp = await client.post(
        "/api/auth/token",
        data={"username": SIGNUP_PAYLOAD["email"], "password": SIGNUP_PAYLOAD["password"]},
    )
    token = resp.json()["access_token"]
    projects = await client.get("/api/projects/", headers={"Authorization": f"Bearer {token}"})
    project_id = projects.json()[0]["id"]
    return token, project_id


@pytest.mark.asyncio
async def test_event_count_not_found(client):
    token, _ = await _get_auth(client)
    resp = await client.get(
        "/api/sessions/nonexistent/events/count",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_token_usage_not_found(client):
    token, _ = await _get_auth(client)
    resp = await client.get(
        "/api/sessions/nonexistent/events/tokens",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_error_events_not_found(client):
    token, _ = await _get_auth(client)
    resp = await client.get(
        "/api/sessions/nonexistent/events/errors",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_latency_percentiles_not_found(client):
    token, _ = await _get_auth(client)
    resp = await client.get(
        "/api/sessions/nonexistent/events/latency",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_model_breakdown_not_found(client):
    token, _ = await _get_auth(client)
    resp = await client.get(
        "/api/sessions/nonexistent/events/models",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_trace_endpoints_require_auth(client):
    for path in [
        "/api/sessions/x/events/count",
        "/api/sessions/x/events/tokens",
        "/api/sessions/x/events/errors",
        "/api/sessions/x/events/latency",
        "/api/sessions/x/events/models",
    ]:
        resp = await client.get(path)
        assert resp.status_code == 401, f"Expected 401 for {path}"
