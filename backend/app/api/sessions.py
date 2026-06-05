from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from ..database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..schemas.session import SessionResponse, LoopInfo
from ..crud.project import get_project
from ..crud.session import (
    get_session,
    list_project_sessions,
    delete_session,
    search_sessions,
)
from ..loop_detector import detect_loops

router = APIRouter()


def _enrich_session(session) -> SessionResponse:
    """Build a SessionResponse with loop-detection results injected."""
    loop_result = detect_loops(session.events or [])
    loop_info = [
        LoopInfo(
            kind=occ.kind,
            description=occ.description,
            event_ids=occ.event_ids,
            repeat_count=occ.repeat_count,
            severity=occ.severity,
        )
        for occ in loop_result.occurrences
    ]
    resp = SessionResponse.model_validate(session)
    resp.loop_detected = loop_result.loop_detected
    resp.loop_info = loop_info

    # Compute duration from events
    if session.events:
        timestamps = [e.timestamp for e in session.events if e.timestamp]
        if len(timestamps) >= 2:
            resp.duration_ms = round(
                (max(timestamps) - min(timestamps)).total_seconds() * 1000, 1
            )
    return resp


@router.get("/", response_model=List[SessionResponse])
async def read_sessions(
    project_id: str,
    skip: int = Query(0, ge=0, description="Number of sessions to skip"),
    limit: int = Query(50, ge=1, le=200, description="Max sessions to return"),
    search: Optional[str] = Query(None, description="Filter by session name (case-insensitive)"),
    tag_key: Optional[str] = Query(None, description="Filter by tag key"),
    tag_value: Optional[str] = Query(None, description="Filter by tag value"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List sessions for a project with optional search and tag filters."""
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    if search or tag_key:
        sessions = await search_sessions(
            db,
            project_id=project_id,
            name_query=search,
            tag_key=tag_key,
            tag_value=tag_value,
            skip=skip,
            limit=limit,
        )
    else:
        sessions = await list_project_sessions(db, project_id=project_id, skip=skip, limit=limit)

    return [_enrich_session(s) for s in sessions]


@router.get("/{session_id}", response_model=SessionResponse)
async def read_session_detail(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    session = await get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    # Verify project owner is current user
    project = await get_project(db, project_id=session.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    return _enrich_session(session)


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session_endpoint(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Soft-delete a session (permanently removes from DB)."""
    session = await get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    project = await get_project(db, project_id=session.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    await delete_session(db, session)


@router.get("/{session_id}/export")
async def export_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export a full session as a downloadable JSON file."""
    session = await get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    project = await get_project(db, project_id=session.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    enriched = _enrich_session(session)
    payload = enriched.model_dump(mode="json")

    return JSONResponse(
        content=payload,
        headers={
            "Content-Disposition": f'attachment; filename="session-{session_id[:8]}.json"',
        },
    )
