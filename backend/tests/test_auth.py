from __future__ import annotations
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_flow(client: AsyncClient):
    # 1. Sign up user
    response = await client.post(
        "/api/auth/signup",
        json={"email": "test@ghostrace.dev", "password": "SecurePass1!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@ghostrace.dev"
    assert "id" in data
    assert data["plan"] == "free"

    # 2. Prevent duplicate signup
    response_dup = await client.post(
        "/api/auth/signup",
        json={"email": "test@ghostrace.dev", "password": "OtherPass2!"},
    )
    assert response_dup.status_code == 400
    assert "already exists" in response_dup.json()["detail"]


@pytest.mark.asyncio
async def test_login_flow(client: AsyncClient):
    # 1. Register a user
    await client.post(
        "/api/auth/signup",
        json={"email": "login@ghostrace.dev", "password": "SecurePass1!"},
    )

    # 2. Login successfully
    response = await client.post(
        "/api/auth/token",
        data={"username": "login@ghostrace.dev", "password": "SecurePass1!"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # 3. Login failure - wrong password
    response_fail = await client.post(
        "/api/auth/token",
        data={"username": "login@ghostrace.dev", "password": "WrongPass2!"},
    )
    assert response_fail.status_code == 401

    # 4. Login failure - non-existent email
    response_not_found = await client.post(
        "/api/auth/token",
        data={"username": "missing@ghostrace.dev", "password": "SecurePass1!"},
    )
    assert response_not_found.status_code == 401
