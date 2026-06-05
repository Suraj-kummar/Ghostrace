from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from .trace_event import TraceEventIngest, TraceEventResponse


class SessionBase(BaseModel):
    id: str
    project_id: str
    name: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    started_at: datetime


class SessionIngest(BaseModel):
    session_id: str
    project: str
    name: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    started_at: datetime
    events: List[TraceEventIngest] = Field(default_factory=list)


class LoopInfo(BaseModel):
    """Details about a single detected loop pattern within a session."""
    kind: str                   # "llm_prompt" | "tool_call" | "consecutive_model"
    description: str
    event_ids: List[str]
    repeat_count: int
    severity: str               # "warning" | "critical"


class SessionResponse(SessionBase):
    created_at: datetime
    events: List[TraceEventResponse] = Field(default_factory=list)
    loop_detected: bool = False
    loop_info: List[LoopInfo] = Field(default_factory=list)
    duration_ms: Optional[float] = None  # computed from first/last event timestamps

    model_config = {"from_attributes": True}

