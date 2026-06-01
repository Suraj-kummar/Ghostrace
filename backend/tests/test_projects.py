from __future__ import annotations
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_projects_and_keys(client: AsyncClient):
    # 1. Sign up and get token
    signup_res = await client.post(
        "/api/auth/signup",
        json={"email": "projects@ghostrace.dev", "password": "password123"},
    )
    assert signup_res.status_code == 201

    token_res = await client.post(
        "/api/auth/token",
        data={"username": "projects@ghostrace.dev", "password": "password123"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Check that the auto-generated default project exists
    list_res = await client.get("/api/projects/", headers=headers)
    assert list_res.status_code == 200
    projects = list_res.json()
    assert len(projects) == 1
    default_project = projects[0]
    assert default_project["name"] == "default"

    # 3. Create a second project - should fail on "free" plan because project limit is 1
    create_res = await client.post(
        "/api/projects/",
        json={"name": "custom-project"},
        headers=headers,
    )
    assert create_res.status_code == 400
    assert "Project limit" in create_res.json()["detail"]

    # 4. Check auto-generated API key
    keys_res = await client.get(f"/api/projects/{default_project['id']}/keys", headers=headers)
    assert keys_res.status_code == 200
    keys = keys_res.json()
    assert len(keys) == 1
    assert keys[0]["key"].startswith("gr_")

    # 5. Try creating another API key - should fail because api_key limit is 1 on free plan
    create_key_res = await client.post(
        f"/api/projects/{default_project['id']}/keys",
        json={"name": "Second Key"},
        headers=headers,
    )
    assert create_key_res.status_code == 400
    assert "API key limit" in create_key_res.json()["detail"]
