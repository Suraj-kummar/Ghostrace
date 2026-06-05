"""
ghostrace.backend.api.traces
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Per-session trace-event analytics endpoints:
  - Event count
  - Token usage aggregation
  - Error event listing
  - Latency percentiles (p50 / p95 / p99)
  - Model usage breakdown
"""
from __future__ import annotations

import statistics
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Dict, List, Optional

from ..database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..models.trace_event import TraceEvent
from ..crud.project import get_project
from ..crud.session import get_session

router = APIRouter(tags=["Trace Events"])


async def _assert_session_ownership(
    db: AsyncSession, session_id: str, user: User
) -> None:
    session = await get_session(db, session_id=session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    project = await get_project(db, project_id=session.project_id)
    if not project or project.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return session


@router.get("/api/sessions/{session_id}/events/count")
async def get_event_count(
    session_id: str,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return total event count for a session, optionally filtered by event_type."""
    await _assert_session_ownership(db, session_id, current_user)

    q = select(func.count(TraceEvent.id)).where(TraceEvent.session_id == session_id)
    if event_type:
        q = q.where(TraceEvent.event_type == event_type)

    result = await db.execute(q)
    count = result.scalar() or 0
    return {"session_id": session_id, "event_type": event_type, "count": count}


@router.get("/api/sessions/{session_id}/events/tokens")
async def get_token_usage(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return aggregated token usage and cost for a session."""
    session = await _assert_session_ownership(db, session_id, current_user)

    events = session.events or []
    total_in = sum(e.tokens_in or 0 for e in events)
    total_out = sum(e.tokens_out or 0 for e in events)
    total_cost = sum(e.cost_usd or 0.0 for e in events)

    return {
        "session_id": session_id,
        "tokens_in": total_in,
        "tokens_out": total_out,
        "total_tokens": total_in + total_out,
        "total_cost_usd": round(total_cost, 6),
    }


@router.get("/api/sessions/{session_id}/events/errors")
async def get_error_events(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all error-type events for a session."""
    session = await _assert_session_ownership(db, session_id, current_user)

    errors = [
        {
            "id": e.id,
            "sequence_number": e.sequence_number,
            "timestamp": e.timestamp.isoformat(),
            "error_type": e.error_type,
            "error_message": e.error_message,
            "stack_trace": e.stack_trace,
        }
        for e in (session.events or [])
        if e.event_type == "error" or e.error_type
    ]
    return {"session_id": session_id, "error_count": len(errors), "errors": errors}


@router.get("/api/sessions/{session_id}/events/latency")
async def get_latency_percentiles(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return p50 / p95 / p99 latency for all LLM call events in a session."""
    session = await _assert_session_ownership(db, session_id, current_user)

    latencies = sorted(
        e.latency_ms for e in (session.events or []) if e.latency_ms is not None
    )

    if not latencies:
        return {"session_id": session_id, "count": 0, "p50": None, "p95": None, "p99": None}

    def percentile(data: List[float], p: float) -> float:
        k = (len(data) - 1) * p / 100
        f, c = int(k), min(int(k) + 1, len(data) - 1)
        return round(data[f] + (data[c] - data[f]) * (k - f), 1)

    return {
        "session_id": session_id,
        "count": len(latencies),
        "min_ms": latencies[0],
        "max_ms": latencies[-1],
        "mean_ms": round(statistics.mean(latencies), 1),
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "p99_ms": percentile(latencies, 99),
    }


@router.get("/api/sessions/{session_id}/events/models")
async def get_model_breakdown(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return per-model call counts, token usage, and cost for a session."""
    session = await _assert_session_ownership(db, session_id, current_user)

    breakdown: Dict[str, dict] = {}
    for e in (session.events or []):
        if e.event_type != "llm_call" or not e.model:
            continue
        rec = breakdown.setdefault(e.model, {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0})
        rec["calls"] += 1
        rec["tokens_in"] += e.tokens_in or 0
        rec["tokens_out"] += e.tokens_out or 0
        rec["cost_usd"] += e.cost_usd or 0.0

    models = sorted(
        [{"model": m, **v, "cost_usd": round(v["cost_usd"], 6)} for m, v in breakdown.items()],
        key=lambda x: x["calls"],
        reverse=True,
    )
    return {"session_id": session_id, "models": models}
