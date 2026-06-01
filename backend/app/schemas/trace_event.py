from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class TraceEventBase(BaseModel):
    id: str
    session_id: str
    sequence_number: int
    event_type: str
    timestamp: datetime
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


class TraceEventIngest(BaseModel):
    id: str
    session_id: str = ""
    sequence_number: int = 0
    event_type: str = "custom"
    timestamp: datetime
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


class TraceEventResponse(TraceEventBase):
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
    }


