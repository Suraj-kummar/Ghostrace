from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional

from ..models.project import Project
from ..models.session import Session
from ..models.trace_event import TraceEvent
from ..schemas.session import SessionIngest


async def get_session(db: AsyncSession, session_id: str) -> Optional[Session]:
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
        .options(selectinload(Session.events))
    )
    return result.scalars().first()


async def list_project_sessions(
    db: AsyncSession, project_id: str, skip: int = 0, limit: int = 100
) -> List[Session]:
    result = await db.execute(
        select(Session)
        .where(Session.project_id == project_id)
        .options(selectinload(Session.events))
        .order_by(Session.started_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_monthly_trace_count(db: AsyncSession, user_id: str) -> int:
    now = datetime.now(timezone.utc)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)

    query = (
        select(func.count(TraceEvent.id))
        .join(Session, TraceEvent.session_id == Session.id)
        .join(Project, Session.project_id == Project.id)
        .where(Project.user_id == user_id, TraceEvent.timestamp >= start_of_month)
    )
    result = await db.execute(query)
    return result.scalar() or 0


async def ingest_session(db: AsyncSession, project_id: str, payload: SessionIngest) -> Session:
    session_id = payload.session_id
    db_session = await get_session(db, session_id)

    if db_session:
        if payload.name:
            db_session.name = payload.name
        if payload.tags:
            current_tags = dict(db_session.tags)
            current_tags.update(payload.tags)
            db_session.tags = current_tags
    else:
        db_session = Session(
            id=session_id,
            project_id=project_id,
            name=payload.name,
            tags=payload.tags,
            started_at=payload.started_at,
        )
        db.add(db_session)
        await db.flush()

    if payload.events:
        event_ids = [e.id for e in payload.events]
        existing_events_res = await db.execute(
            select(TraceEvent.id).where(TraceEvent.id.in_(event_ids))
        )
        existing_event_ids = set(existing_events_res.scalars().all())

        for e_schema in payload.events:
            if e_schema.id in existing_event_ids:
                continue

            db_event = TraceEvent(
                id=e_schema.id,
                session_id=session_id,
                sequence_number=e_schema.sequence_number,
                event_type=e_schema.event_type,
                timestamp=e_schema.timestamp,
                model=e_schema.model,
                prompt=e_schema.prompt,
                response=e_schema.response,
                tokens_in=e_schema.tokens_in,
                tokens_out=e_schema.tokens_out,
                cost_usd=e_schema.cost_usd,
                latency_ms=e_schema.latency_ms,
                tool_name=e_schema.tool_name,
                tool_input=e_schema.tool_input,
                tool_output=e_schema.tool_output,
                error_type=e_schema.error_type,
                error_message=e_schema.error_message,
                stack_trace=e_schema.stack_trace,
                metadata_json=e_schema.metadata,
            )
            db.add(db_event)

        await db.flush()

    # Re-fetch session to load events relationship properly
    db_session = await get_session(db, session_id)
    return db_session  # type: ignore[return-value]


async def delete_session(db: AsyncSession, session: "Session") -> None:
    """Permanently delete a session and its events (cascade)."""
    await db.delete(session)
    await db.flush()


async def search_sessions(
    db: AsyncSession,
    project_id: str,
    name_query: Optional[str] = None,
    tag_key: Optional[str] = None,
    tag_value: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List["Session"]:
    """Search sessions by name substring and/or tag key/value."""
    from ..models.session import Session as SessionModel  # local import to avoid circular

    q = (
        select(SessionModel)
        .where(SessionModel.project_id == project_id)
        .options(selectinload(SessionModel.events))
        .order_by(SessionModel.started_at.desc())
    )

    if name_query:
        q = q.where(SessionModel.name.ilike(f"%{name_query}%"))

    # JSON tag filtering — works for SQLite and PostgreSQL JSON columns
    if tag_key and tag_value:
        # SQLite JSON path operator
        q = q.where(
            func.json_extract(SessionModel.tags, f"$.{tag_key}") == tag_value
        )
    elif tag_key:
        q = q.where(
            func.json_extract(SessionModel.tags, f"$.{tag_key}") != None  # noqa: E711
        )

    q = q.offset(skip).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())
