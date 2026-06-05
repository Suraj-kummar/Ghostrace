"""Tests for analytics endpoint."""
from __future__ import annotations
import pytest


SIGNUP_PAYLOAD = {
    "email": "analytics_test@example.com",
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
async def test_analytics_empty_project(client):
    token, project_id = await _get_auth(client)
    resp = await client.get(
        f"/api/projects/{project_id}/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_sessions"] == 0
    assert data["total_events"] == 0
    assert isinstance(data["daily"], list)
    assert len(data["daily"]) == 30  # default period


@pytest.mark.asyncio
async def test_analytics_custom_period(client):
    token, project_id = await _get_auth(client)
    resp = await client.get(
        f"/api/projects/{project_id}/analytics",
        params={"period_days": 7},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["period_days"] == 7
    assert len(data["daily"]) == 7


@pytest.mark.asyncio
async def test_analytics_not_found(client):
    token, _ = await _get_auth(client)
    resp = await client.get(
        "/api/projects/nonexistent/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_analytics_requires_auth(client):
    resp = await client.get("/api/projects/some-id/analytics")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_analytics_has_weekly_field(client):
    token, project_id = await _get_auth(client)
    resp = await client.get(
        f"/api/projects/{project_id}/analytics",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "weekly" in data
    assert "error_rate_daily" in data
    assert "top_models" in data
