from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone, timedelta
from collections import defaultdict

from ..database import get_db
from ..api.deps import get_current_user
from ..models.user import User
from ..models.session import Session
from ..crud.project import get_project
from ..loop_detector import detect_loops
from ..schemas.analytics import (
    AnalyticsResponse,
    DailyMetric,
    WeeklyTrend,
    ModelStat,
    ErrorRatePoint,
)

router = APIRouter()


@router.get("/{project_id}/analytics", response_model=AnalyticsResponse)
async def get_project_analytics(
    project_id: str,
    period_days: int = Query(30, ge=7, le=365, description="Days to look back"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auth check
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    cutoff = datetime.now(timezone.utc) - timedelta(days=period_days)

    # ── 1. Fetch all sessions with events (within period) ─────────────────
    from sqlalchemy.orm import selectinload
    sessions_res = await db.execute(
        select(Session)
        .where(Session.project_id == project_id, Session.started_at >= cutoff)
        .options(selectinload(Session.events))
        .order_by(Session.started_at.asc())
    )
    sessions = list(sessions_res.scalars().all())

    # ── 2. Aggregate daily buckets ─────────────────────────────────────────
    daily: dict[str, dict] = {}
    for i in range(period_days):
        day = (datetime.now(timezone.utc) - timedelta(days=period_days - 1 - i)).strftime("%Y-%m-%d")
        daily[day] = {"sessions": 0, "events": 0, "cost_usd": 0.0, "tokens": 0, "errors": 0, "error_sessions": 0}

    weekly: dict[str, dict] = defaultdict(lambda: {"sessions": 0, "events": 0, "cost_usd": 0.0})
    model_stats: dict[str, dict] = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0})

    total_events = 0
    total_cost = 0.0
    total_tokens = 0
    error_sessions = 0
    loop_sessions = 0
    latency_sum = 0.0
    latency_count = 0
    duration_sum = 0.0
    duration_count = 0

    for sess in sessions:
        day_key = sess.started_at.strftime("%Y-%m-%d")
        week_key = sess.started_at.strftime("%G-W%V")

        if day_key not in daily:
            continue

        daily[day_key]["sessions"] += 1
        weekly[week_key]["sessions"] += 1
        sess_has_error = False

        # Session duration from first/last event timestamps
        if sess.events:
            ts_list = [e.timestamp for e in sess.events if e.timestamp]
            if len(ts_list) >= 2:
                dur_ms = (max(ts_list) - min(ts_list)).total_seconds() * 1000
                duration_sum += dur_ms
                duration_count += 1

        for ev in (sess.events or []):
            total_events += 1
            daily[day_key]["events"] += 1
            weekly[week_key]["events"] += 1

            cost = ev.cost_usd or 0.0
            tokens = (ev.tokens_in or 0) + (ev.tokens_out or 0)
            total_cost += cost
            total_tokens += tokens
            daily[day_key]["cost_usd"] += cost
            weekly[week_key]["cost_usd"] += cost
            daily[day_key]["tokens"] += tokens

            if ev.event_type == "error" or ev.error_type:
                sess_has_error = True
                daily[day_key]["errors"] += 1

            if ev.latency_ms:
                latency_sum += ev.latency_ms
                latency_count += 1

            if ev.event_type == "llm_call" and ev.model:
                model_stats[ev.model]["calls"] += 1
                model_stats[ev.model]["tokens"] += (ev.tokens_in or 0) + (ev.tokens_out or 0)
                model_stats[ev.model]["cost_usd"] += cost

        if sess_has_error:
            error_sessions += 1
            daily[day_key]["error_sessions"] += 1

        result = detect_loops(sess.events or [])
        if result.loop_detected:
            loop_sessions += 1

    # ── 3. Build response ──────────────────────────────────────────────────
    daily_list = [
        DailyMetric(
            date=date,
            sessions=v["sessions"],
            events=v["events"],
            cost_usd=round(v["cost_usd"], 6),
            tokens=v["tokens"],
            errors=v["errors"],
        )
        for date, v in sorted(daily.items())
    ]

    weekly_list = [
        WeeklyTrend(
            week=week,
            sessions=v["sessions"],
            events=v["events"],
            cost_usd=round(v["cost_usd"], 6),
        )
        for week, v in sorted(weekly.items())
    ]

    # Error rate per day
    error_rate_daily = [
        ErrorRatePoint(
            date=date,
            total_sessions=v["sessions"],
            error_sessions=v["error_sessions"],
            error_rate=round(v["error_sessions"] / v["sessions"], 4) if v["sessions"] else 0.0,
        )
        for date, v in sorted(daily.items())
    ]

    # Top models sorted by cost (descending)
    top_models = sorted(
        [
            ModelStat(
                model=model,
                calls=s["calls"],
                tokens=s["tokens"],
                cost_usd=round(s["cost_usd"], 6),
            )
            for model, s in model_stats.items()
        ],
        key=lambda m: m.cost_usd,
        reverse=True,
    )[:8]

    return AnalyticsResponse(
        period_days=period_days,
        total_sessions=len(sessions),
        total_events=total_events,
        total_cost_usd=round(total_cost, 6),
        total_tokens=total_tokens,
        error_sessions=error_sessions,
        loop_sessions=loop_sessions,
        avg_latency_ms=round(latency_sum / latency_count, 1) if latency_count else 0.0,
        avg_session_duration_ms=round(duration_sum / duration_count, 1) if duration_count else None,
        daily=daily_list,
        weekly=weekly_list,
        top_models=top_models,
        error_rate_daily=error_rate_daily,
    )



@router.get("/{project_id}/analytics", response_model=AnalyticsResponse)
async def get_project_analytics(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Auth check
    project = await get_project(db, project_id=project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    cutoff = datetime.now(timezone.utc) - timedelta(days=PERIOD_DAYS)

    # ── 1. Fetch all sessions with events (within period) ─────────────────
    from sqlalchemy.orm import selectinload
    sessions_res = await db.execute(
        select(Session)
        .where(Session.project_id == project_id, Session.started_at >= cutoff)
        .options(selectinload(Session.events))
        .order_by(Session.started_at.asc())
    )
    sessions = list(sessions_res.scalars().all())

    # ── 2. Aggregate daily buckets ─────────────────────────────────────────
    daily: dict[str, dict] = {}
    # Pre-fill all days in range so chart has no gaps
    for i in range(PERIOD_DAYS):
        day = (datetime.now(timezone.utc) - timedelta(days=PERIOD_DAYS - 1 - i)).strftime("%Y-%m-%d")
        daily[day] = {"sessions": 0, "events": 0, "cost_usd": 0.0, "tokens": 0, "errors": 0}

    model_stats: dict[str, dict] = defaultdict(lambda: {"calls": 0, "tokens": 0, "cost_usd": 0.0})

    total_events = 0
    total_cost = 0.0
    total_tokens = 0
    error_sessions = 0
    loop_sessions = 0
    latency_sum = 0.0
    latency_count = 0

    for sess in sessions:
        day_key = sess.started_at.strftime("%Y-%m-%d")
        if day_key not in daily:
            continue

        daily[day_key]["sessions"] += 1
        sess_has_error = False

        for ev in (sess.events or []):
            total_events += 1
            daily[day_key]["events"] += 1

            cost = ev.cost_usd or 0.0
            tokens = (ev.tokens_in or 0) + (ev.tokens_out or 0)
            total_cost += cost
            total_tokens += tokens
            daily[day_key]["cost_usd"] += cost
            daily[day_key]["tokens"] += tokens

            if ev.event_type == "error" or ev.error_type:
                sess_has_error = True
                daily[day_key]["errors"] += 1

            if ev.latency_ms:
                latency_sum += ev.latency_ms
                latency_count += 1

            if ev.event_type == "llm_call" and ev.model:
                model_stats[ev.model]["calls"] += 1
                model_stats[ev.model]["tokens"] += (ev.tokens_in or 0) + (ev.tokens_out or 0)
                model_stats[ev.model]["cost_usd"] += cost

        if sess_has_error:
            error_sessions += 1

        # Loop detection
        result = detect_loops(sess.events or [])
        if result.loop_detected:
            loop_sessions += 1

    # ── 3. Build response ──────────────────────────────────────────────────
    daily_list = [
        DailyMetric(
            date=date,
            sessions=v["sessions"],
            events=v["events"],
            cost_usd=round(v["cost_usd"], 6),
            tokens=v["tokens"],
            errors=v["errors"],
        )
        for date, v in sorted(daily.items())
    ]

    top_models = sorted(
        [
            ModelStat(
                model=model,
                calls=s["calls"],
                tokens=s["tokens"],
                cost_usd=round(s["cost_usd"], 6),
            )
            for model, s in model_stats.items()
        ],
        key=lambda m: m.calls,
        reverse=True,
    )[:8]

    return AnalyticsResponse(
        period_days=PERIOD_DAYS,
        total_sessions=len(sessions),
        total_events=total_events,
        total_cost_usd=round(total_cost, 6),
        total_tokens=total_tokens,
        error_sessions=error_sessions,
        loop_sessions=loop_sessions,
        avg_latency_ms=round(latency_sum / latency_count, 1) if latency_count else 0.0,
        daily=daily_list,
        top_models=top_models,
    )
