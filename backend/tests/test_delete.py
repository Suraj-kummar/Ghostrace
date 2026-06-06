from __future__ import annotations
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_delete_project_and_key(client: AsyncClient, settings):
    # Temporarily lift plan limits so this test isn't blocked by the 1-project cap
    original_free = dict(settings.plan_limits["free"])
    settings.plan_limits["free"] = {"traces": -1, "retention_days": 30, "projects": -1, "api_keys": -1}
    try:
        await _run_delete_test(client, settings)
    finally:
        settings.plan_limits["free"] = original_free


async def _run_delete_test(client: AsyncClient, settings):
    # 1. Sign up + login
    await client.post(
        "/api/auth/signup",
        json={"email": "delete@ghostrace.dev", "password": "SecurePass1!"},
    )
    token_res = await client.post(
        "/api/auth/token",
        data={"username": "delete@ghostrace.dev", "password": "SecurePass1!"},
    )
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create a dedicated project for deletion testing
    proj_res = await client.post(
        "/api/projects/",
        json={"name": "to-delete"},
        headers=headers,
    )
    assert proj_res.status_code == 201, proj_res.text
    proj_id = proj_res.json()["id"]

    # 3. Generate an API key on the new project
    key_res = await client.post(
        f"/api/projects/{proj_id}/keys",
        json={"name": "temp-key"},
        headers=headers,
    )
    assert key_res.status_code == 201
    key_id = key_res.json()["id"]

    # 4. Delete the API key — expect 204 No Content
    del_key_res = await client.delete(
        f"/api/projects/{proj_id}/keys/{key_id}",
        headers=headers,
    )
    assert del_key_res.status_code == 204

    # Key should no longer appear in the list
    keys_after = await client.get(f"/api/projects/{proj_id}/keys", headers=headers)
    assert all(k["id"] != key_id for k in keys_after.json())

    # 5. Delete the project — expect 204 No Content
    del_proj_res = await client.delete(
        f"/api/projects/{proj_id}",
        headers=headers,
    )
    assert del_proj_res.status_code == 204

    # Project should no longer appear in the list
    proj_list = await client.get("/api/projects/", headers=headers)
    assert all(p["id"] != proj_id for p in proj_list.json())

    # 6. Deleting same project again should 404
    double_del = await client.delete(f"/api/projects/{proj_id}", headers=headers)
    assert double_del.status_code == 404

    # 7. Bad token should 401
    bad_headers = {"Authorization": "Bearer bad_token"}
    res = await client.delete(f"/api/projects/{proj_id}", headers=bad_headers)
    assert res.status_code == 401
