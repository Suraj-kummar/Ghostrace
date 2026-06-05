from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ..database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..schemas.session import SessionResponse, LoopInfo
from ..crud.project import get_project
from ..crud.session import get_session, list_project_sessions
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
    return resp


@router.get("/", response_model=List[SessionResponse])
async def read_sessions(
    project_id: str,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify project exists and belongs to current user
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

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
