from __future__ import annotations
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.app.models.user import User


@pytest.mark.asyncio
async def test_ingest_flow(client: AsyncClient, db_session: AsyncSession, settings):
    # 1. Sign up user
    signup_res = await client.post(
        "/api/auth/signup",
        json={"email": "ingest@ghostrace.dev", "password": "SecurePass1!"},
    )
    assert signup_res.status_code == 201
    user_id = signup_res.json()["id"]

    token_res = await client.post(
        "/api/auth/token",
        data={"username": "ingest@ghostrace.dev", "password": "SecurePass1!"},
    )
    assert token_res.status_code == 200
    token = token_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get the project and api key
    proj_res = await client.get("/api/projects/", headers=headers)
    project = proj_res.json()[0]
    project_id = project["id"]

    keys_res = await client.get(f"/api/projects/{project_id}/keys", headers=headers)
    api_key_value = keys_res.json()[0]["key"]

    # 3. Successful Ingestion
    payload = {
        "session_id": "session-123",
        "project": "default",
        "name": "test-session",
        "tags": {"env": "test"},
        "started_at": "2026-06-01T00:00:00Z",
        "events": [
            {
                "id": "event-1",
                "sequence_number": 1,
                "event_type": "llm_call",
                "timestamp": "2026-06-01T00:00:01Z",
                "model": "gpt-4o",
                "prompt": "Hello",
                "response": "World",
                "tokens_in": 10,
                "tokens_out": 20,
                "cost_usd": 0.00015,
                "latency_ms": 120,
            }
        ]
    }

    ingest_headers = {"Authorization": f"Bearer {api_key_value}"}
    ingest_res = await client.post("/v1/ingest", json=payload, headers=ingest_headers)
    assert ingest_res.status_code == 201
    assert ingest_res.json()["status"] == "ok"

    # 4. Verify dashboard endpoints read the ingested session
    session_res = await client.get(f"/api/sessions/?project_id={project_id}", headers=headers)
    assert session_res.status_code == 200
    sessions = session_res.json()
    assert len(sessions) == 1
    assert sessions[0]["id"] == "session-123"
    assert sessions[0]["name"] == "test-session"
    assert sessions[0]["tags"] == {"env": "test"}

    # Read details
    detail_res = await client.get("/api/sessions/session-123", headers=headers)
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert len(detail["events"]) == 1
    assert detail["events"][0]["id"] == "event-1"
    assert detail["events"][0]["model"] == "gpt-4o"
    assert detail["events"][0]["metadata"] == {}

    # 5. Ingestion validation: Project mismatch should fail
    payload_bad_project = dict(payload)
    payload_bad_project["project"] = "other-project"
    payload_bad_project["session_id"] = "session-124"
    res_bad_project = await client.post("/v1/ingest", json=payload_bad_project, headers=ingest_headers)
    assert res_bad_project.status_code == 400

    # 6. Ingestion validation: Invalid API key should fail
    res_bad_key = await client.post("/v1/ingest", json=payload, headers={"Authorization": "Bearer gr_invalid"})
    assert res_bad_key.status_code == 401

    # 7. Ingestion validation: Rate limit checks
    # Add a mock low limit plan to settings config
    settings.plan_limits["limited_plan"] = {"traces": 2, "retention_days": 7, "projects": 1, "api_keys": 1}

    # Update the user plan to limited_plan in database
    db_user_res = await db_session.execute(select(User).where(User.id == user_id))
    db_user = db_user_res.scalars().first()
    db_user.plan = "limited_plan"
    await db_session.commit()

    # Now, ingest 2nd event (currently we have 1 event in db)
    payload_event_2 = {
        "session_id": "session-123",
        "project": "default",
        "started_at": "2026-06-01T00:00:00Z",
        "events": [
            {
                "id": "event-2",
                "sequence_number": 2,
                "event_type": "tool_call",
                "timestamp": "2026-06-01T00:00:02Z",
                "tool_name": "search",
            }
        ]
    }
    res_2 = await client.post("/v1/ingest", json=payload_event_2, headers=ingest_headers)
    assert res_2.status_code == 201

    # Now, try to ingest a 3rd event — should exceed limit of 2 and raise 429
    payload_event_3 = {
        "session_id": "session-123",
        "project": "default",
        "started_at": "2026-06-01T00:00:00Z",
        "events": [
            {
                "id": "event-3",
                "sequence_number": 3,
                "event_type": "custom",
                "timestamp": "2026-06-01T00:00:03Z",
            }
        ]
    }
    res_3 = await client.post("/v1/ingest", json=payload_event_3, headers=ingest_headers)
    assert res_3.status_code == 429
    assert "limit exceeded" in res_3.json()["detail"]
