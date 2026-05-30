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

# Stack of session IDs (innermost last)
_SESSION_STACK: ContextVar[list[str]] = ContextVar("_ghostrace_session_stack", default=[])
_SESSION_REGISTRY: Dict[str, "Session"] = {}


def get_current_session_id() -> Optional[str]:
    """Return the innermost open session ID, or None."""
    stack = _SESSION_STACK.get()
    return stack[-1] if stack else None


def get_session(session_id: str) -> Optional["Session"]:
    return _SESSION_REGISTRY.get(session_id)


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

    def __init__(
        self,
        name: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        self.id: str = session_id or str(uuid.uuid4())
        self.name: Optional[str] = name
        self.tags: Dict[str, str] = {}
        self.started_at: datetime = datetime.now(timezone.utc)
        self.ended_at: Optional[datetime] = None

        # contextvars token — used to restore previous stack on exit
        self._token: Optional[Token[list[str]]] = None

    # ── Tag API ──────────────────────────────────────────────────────────────

    def tag(self, key: str, value: str) -> "Session":
        """Attach a key/value tag to this session (chainable)."""
        self.tags[key] = str(value)
        return self

    # ── Sync context manager ─────────────────────────────────────────────────

    def __enter__(self) -> "Session":
        self._open()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self._close(error=exc_type is not None)

    # ── Async context manager ────────────────────────────────────────────────

    async def __aenter__(self) -> "Session":
        self._open()
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self._close(error=exc_type is not None)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _open(self) -> None:
        current_stack = _SESSION_STACK.get()[:]  # copy
        current_stack.append(self.id)
        self._token = _SESSION_STACK.set(current_stack)
        _SESSION_REGISTRY[self.id] = self

    def _close(self, *, error: bool = False) -> None:
        self.ended_at = datetime.now(timezone.utc)

        # Flush to collector
        try:
            from .collector import get_collector

            get_collector().flush_session(self, error=error)
        except Exception:  # noqa: BLE001
            pass

        # Pop this session off the stack
        if self._token is not None:
            _SESSION_STACK.reset(self._token)

        _SESSION_REGISTRY.pop(self.id, None)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def duration_ms(self) -> Optional[int]:
        if self.ended_at:
            delta = self.ended_at - self.started_at
            return int(delta.total_seconds() * 1000)
        return None

    def __repr__(self) -> str:
        return f"Session(id={self.id!r}, name={self.name!r})"
