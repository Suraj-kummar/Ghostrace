from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...config import get_settings
from ...api.deps import get_api_key
from ...models.api_key import ApiKey
from ...models.project import Project
from ...models.user import User
from ...schemas.session import SessionIngest
from ...crud.session import get_monthly_trace_count, ingest_session
from ...crud.user import get_user

router = APIRouter()


@router.post("/ingest", status_code=status.HTTP_201_CREATED)
async def ingest(
    payload: SessionIngest,
    db: AsyncSession = Depends(get_db),
    api_key: ApiKey = Depends(get_api_key),
):
    # 1. Verify project name matches the API Key's project
    project = api_key.project
    if project.name != payload.project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"API key is associated with project '{project.name}', but payload specified '{payload.project}'",
        )

    # 2. Get user to check plan limits
    user = await get_user(db, project.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project owner not found",
        )

    # 3. Check monthly trace limits
    settings = get_settings()
    plan = user.plan.lower()
    limits = settings.plan_limits.get(plan, settings.plan_limits["free"])
    max_traces = limits.get("traces", 50000)

    if max_traces != -1:
        current_traces = await get_monthly_trace_count(db, user.id)
        incoming_traces = len(payload.events)
        if current_traces + incoming_traces > max_traces:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Trace limit exceeded for current plan",
            )

    # 4. Ingest session and events
    await ingest_session(db, project.id, payload)
    return {"status": "ok", "session_id": payload.session_id}
