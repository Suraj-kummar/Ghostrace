"""
ghostrace.backend.api.health
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Kubernetes-style health check endpoints: /health/live and /health/ready.
"""
from __future__ import annotations

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..database import get_db

router = APIRouter(tags=["Health"])

_start_time = datetime.now(timezone.utc)


@router.get("/health/live")
async def liveness():
    """Liveness probe — returns 200 if the process is alive."""
    return {
        "status": "alive",
        "uptime_seconds": round(
            (datetime.now(timezone.utc) - _start_time).total_seconds(), 1
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness probe — returns 200 only if the DB connection is healthy."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as exc:  # pragma: no cover
        db_status = f"error: {exc}"

    return {
        "status": "ready" if db_status == "ok" else "not_ready",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
