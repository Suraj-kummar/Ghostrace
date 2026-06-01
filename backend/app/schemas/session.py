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


class SessionResponse(SessionBase):
    created_at: datetime
    events: List[TraceEventResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}
