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
        self._lock = threading.Lock()
        # session_id → list of events (in order received)
        self._sessions: DefaultDict[str, List[TraceEvent]] = defaultdict(list)
        # session_id → next sequence number
        self._seq: DefaultDict[str, int] = defaultdict(int)

    def record(self, event: TraceEvent) -> None:
        """
        Accept a TraceEvent, attach session context, write locally,
        and (if not local_only) enqueue for HTTP send.

        This must NEVER raise — all errors are caught here.
        """
        try:
            from .session import get_current_session_id

            session_id = event.session_id or get_current_session_id() or _anonymous_session_id()
            event.session_id = session_id

            with self._lock:
                seq = self._seq[session_id]
                self._seq[session_id] += 1
                event.sequence_number = seq
                self._sessions[session_id].append(event)

            # Always write locally
            write_event(event.to_dict())

            # HTTP send (non-local_only, single-event sessions or immediate mode)
            config = get_config()
            if not config.local_only and config.is_configured():
                # For single-event sends (no explicit session), flush immediately
                if not _is_inside_session(session_id):
                    self._send_immediately(session_id, event)

        except Exception as exc:  # noqa: BLE001
            logger.warning("ghostrace: collector.record error: %s", exc)

    def flush_session(self, session_obj: "Any", *, error: bool = False) -> None:  # noqa: F821
        """
        Called by Session.__exit__ — send all accumulated events as one batch.
        """
        try:
            config = get_config()
            session_id = session_obj.id
            events: List[TraceEvent] = []

            with self._lock:
                events = self._sessions.pop(session_id, [])
                self._seq.pop(session_id, None)

            if not events:
                return

            payload = SessionPayload(
                session_id=session_id,
                project=config.project,
                name=session_obj.name,
                tags=session_obj.tags,
                started_at=session_obj.started_at,
                events=events,
            )

            if not config.local_only and config.is_configured():
                from .sender import get_sender

                get_sender().enqueue(payload.to_dict())

        except Exception as exc:  # noqa: BLE001
            logger.warning("ghostrace: collector.flush_session error: %s", exc)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _send_immediately(self, session_id: str, event: TraceEvent) -> None:
        """Send a single-event payload without waiting for session close."""
        try:
            from .sender import get_sender

            config = get_config()
            payload = SessionPayload(
                session_id=session_id,
                project=config.project,
                events=[event],
            )
            get_sender().enqueue(payload.to_dict())

            # Clean up inline-session state
            with self._lock:
                self._sessions.pop(session_id, None)
                self._seq.pop(session_id, None)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ghostrace: _send_immediately error: %s", exc)


def _anonymous_session_id() -> str:
    """Generate and cache a per-process anonymous session ID."""
    global _anon_session_id
    if _anon_session_id is None:
        import uuid

        _anon_session_id = str(uuid.uuid4())
    return _anon_session_id


def _is_inside_session(session_id: str) -> bool:
    """Return True if this session_id is an explicit user session (not anonymous)."""
    from .session import _SESSION_REGISTRY

    return session_id in _SESSION_REGISTRY


_anon_session_id: Optional[str] = None

# ── Module-level singleton ────────────────────────────────────────────────────
_collector: Optional[EventCollector] = None


def get_collector() -> EventCollector:
    global _collector
    if _collector is None:
        _collector = EventCollector()
    return _collector
