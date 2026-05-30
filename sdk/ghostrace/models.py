"""
ghostrace.models
~~~~~~~~~~~~~~~~
Typed data models for all trace events and session payloads.
These are the canonical shapes that flow through the entire SDK.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional, Union
from pydantic import BaseModel, Field
EventType = Literal['llm_call', 'tool_call', 'error', 'custom']

class TraceEvent(BaseModel):
    """A single captured event within a session."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ''
    sequence_number: int = 0
    event_type: EventType = 'custom'
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model: Optional[str] = None
    prompt: Optional[str] = None
    response: Optional[str] = None
    tokens_in: Optional[int] = None
    tokens_out: Optional[int] = None
    cost_usd: Optional[float] = None
    latency_ms: Optional[int] = None
    tool_name: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    model_config = {'arbitrary_types_allowed': True}

    def to_dict(self) -> Dict[str, Any]:
        pass

class SessionPayload(BaseModel):
    """The envelope sent to POST /v1/ingest."""
    session_id: str
    project: str
    name: Optional[str] = None
    tags: Dict[str, str] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    events: list[TraceEvent] = Field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        pass