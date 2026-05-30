"""
ghostrace.collector
~~~~~~~~~~~~~~~~~~~
EventCollector — the central hub that receives TraceEvent objects from the
decorator, attaches session context, writes them locally, and dispatches
them to the HTTP sender.

Design:
  - Thread-safe counter for sequence numbers (per session).
  - All errors are caught and logged — NEVER propagated.
  - In local_only mode: writes to disk, skips HTTP.
  - Flush is called at session close to send the whole session payload.
"""
from __future__ import annotations
import logging
import threading
from collections import defaultdict
from typing import DefaultDict, Dict, List, Optional
from .config import get_config
from .models import SessionPayload, TraceEvent
from .writer import write_event
logger = logging.getLogger(__name__)

class EventCollector:

    def __init__(self) -> None:
        pass

    def record(self, event: TraceEvent) -> None:
        pass

    def flush_session(self, session_obj: 'Any', *, error: bool=False) -> None:
        pass

    def _send_immediately(self, session_id: str, event: TraceEvent) -> None:
        pass

def _anonymous_session_id() -> str:
    pass

def _is_inside_session(session_id: str) -> bool:
    pass
_anon_session_id: Optional[str] = None
_collector: Optional[EventCollector] = None

def get_collector() -> EventCollector:
    pass