from __future__ import annotations
from typing import List
from pydantic import BaseModel


class DailyMetric(BaseModel):
    date: str          # "YYYY-MM-DD"
    sessions: int
    events: int
    cost_usd: float
    tokens: int
    errors: int


class ModelStat(BaseModel):
    model: str
    calls: int
    tokens: int
    cost_usd: float


class AnalyticsResponse(BaseModel):
    period_days: int
    total_sessions: int
    total_events: int
    total_cost_usd: float
    total_tokens: int
    error_sessions: int
    loop_sessions: int
    avg_latency_ms: float
    daily: List[DailyMetric]
    top_models: List[ModelStat]
