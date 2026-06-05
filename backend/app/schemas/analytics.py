"""
ghostrace.backend.schemas.analytics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pydantic schemas for analytics API responses.
Extended with weekly trends, error rate, and avg duration.
"""
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class DailyMetric(BaseModel):
    date: str          # YYYY-MM-DD
    sessions: int
    events: int
    cost_usd: float
    tokens: int
    errors: int


class WeeklyTrend(BaseModel):
    week: str          # ISO week label e.g. "2026-W22"
    sessions: int
    events: int
    cost_usd: float


class ModelStat(BaseModel):
    model: str
    calls: int
    tokens: int
    cost_usd: float


class ErrorRatePoint(BaseModel):
    date: str
    total_sessions: int
    error_sessions: int
    error_rate: float  # 0.0–1.0


class AnalyticsResponse(BaseModel):
    period_days: int
    total_sessions: int
    total_events: int
    total_cost_usd: float
    total_tokens: int
    error_sessions: int
    loop_sessions: int
    avg_latency_ms: float
    avg_session_duration_ms: Optional[float] = None
    daily: List[DailyMetric]
    weekly: List[WeeklyTrend] = []
    top_models: List[ModelStat]
    error_rate_daily: List[ErrorRatePoint] = []
