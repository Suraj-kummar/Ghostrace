"""
ghostrace.session
~~~~~~~~~~~~~~~~~
Session context manager — groups multiple trace events under one logical
"agent run" with a shared session ID.

Usage:
    # Sync
    with ghostrace.session(name="user-request-abc") as s:
        s.tag("user_id", "u_123")
        result = my_agent.run(prompt)

    # Async
    async with ghostrace.session(name="async-run") as s:
        result = await my_async_agent.run(prompt)

Sessions are stored on a contextvars.ContextVar so they work correctly
across threads and asyncio tasks without any global mutation.

Nesting: the innermost open session wins — inner events attach to the
inner session. When the inner session closes, events revert to the outer.
"""
from __future__ import annotations
import uuid
from contextvars import ContextVar, Token
from datetime import datetime, timezone
from typing import Dict, Optional
_SESSION_STACK: ContextVar[list[str]] = ContextVar('_ghostrace_session_stack', default=[])
_SESSION_REGISTRY: Dict[str, 'Session'] = {}

def get_current_session_id() -> Optional[str]:
    pass

def get_session(session_id: str) -> Optional['Session']:
    pass

class Session:
    """
    A context manager that groups trace events into one logical session.

    Attributes:
        id:         UUID string — the session identifier.
        name:       Optional human-readable name (shown in the dashboard).
        tags:       Dict of string key/value pairs for filtering.
        started_at: UTC timestamp when the session opened.
        ended_at:   UTC timestamp when the session closed (set on exit).
    """

    def __init__(self, name: Optional[str]=None, session_id: Optional[str]=None) -> None:
        pass

    def tag(self, key: str, value: str) -> 'Session':
        pass

    def __enter__(self) -> 'Session':
        pass

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    async def __aenter__(self) -> 'Session':
        pass

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        pass

    def _open(self) -> None:
        pass

    def _close(self, *, error: bool=False) -> None:
        pass

    def duration_ms(self) -> Optional[int]:
        pass

    def __repr__(self) -> str:
        pass