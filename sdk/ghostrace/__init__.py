"""
ghostrace
~~~~~~~~~
AI agent observability — full session replay, cost tracking, loop detection.

Quick start::

    import ghostrace

    ghostrace.init(api_key="gr_xxxx", project="my-agent")

    @ghostrace.trace
    def call_llm(prompt: str) -> str:
        ...

    @ghostrace.trace(kind="tool")
    def search_web(query: str) -> list:
        ...

    with ghostrace.session(name="user-request-abc") as s:
        s.tag("user_id", "u_123")
        result = my_agent.run(user_input)

    # Standalone tag on the current active session
    ghostrace.tag("environment", "production")

    # Zero-touch instrumentation (wraps openai / anthropic / langchain / etc.)
    ghostrace.auto_instrument()

    # Flush pending events immediately (useful before process exits)
    ghostrace.flush()
"""
from __future__ import annotations

import logging
from typing import Optional

from .auto_instrument import auto_instrument
from .config import GhostraceConfig, get_config, init
from .decorator import trace
from .session import Session, get_current_session_id, get_session

logger = logging.getLogger(__name__)

__version__ = "0.2.0"
__all__ = [
    "init",
    "trace",
    "session",
    "auto_instrument",
    "tag",
    "flush",
    "current_session",
    "get_config",
    "GhostraceConfig",
    "Session",
    "__version__",
]


def session(
    name: Optional[str] = None,
    session_id: Optional[str] = None,
) -> Session:
    """
    Create a session context manager that groups trace events.

    Usage::

        with ghostrace.session(name="my-run") as s:
            s.tag("env", "prod")
            result = agent.run(prompt)

        # Async
        async with ghostrace.session(name="async-run") as s:
            result = await agent.run(prompt)

    Args:
        name:       Optional human-readable label shown in the dashboard.
        session_id: Optional UUID string. Auto-generated if not provided.

    Returns:
        A :class:`Session` context manager.
    """
    return Session(name=name, session_id=session_id)


def tag(key: str, value: str) -> None:
    """
    Attach a key/value tag to the currently active session.

    This is a module-level convenience wrapper around ``session.tag()``.
    If no session is active, the call is silently ignored.

    Usage::

        with ghostrace.session(name="run") as s:
            ghostrace.tag("user_id", "u_123")  # same as s.tag(...)
            result = agent.run(prompt)

    Args:
        key:   Tag key string.
        value: Tag value string.
    """
    try:
        sid = get_current_session_id()
        if sid is None:
            logger.debug("ghostrace.tag() called outside a session — ignored.")
            return
        sess = get_session(sid)
        if sess is not None:
            sess.tag(key, value)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace.tag() error: %s", exc)


def flush() -> None:
    """
    Block until all queued trace events have been sent (or buffered locally).

    Call this before your process exits to ensure no events are lost::

        import atexit
        import ghostrace

        ghostrace.init(api_key="gr_xxxx", project="my-agent")
        atexit.register(ghostrace.flush)

    In normal usage the background sender drains automatically; this is only
    needed when you want a synchronous guarantee (e.g. in scripts or tests).
    """
    try:
        from .sender import get_sender
        sender = get_sender()
        # Signal the worker and give it up to 5 seconds to drain
        import threading
        done = threading.Event()

        def _ping() -> None:
            try:
                # Put a no-op callable in the queue that sets the event
                import asyncio
                loop = sender._loop
                if loop:
                    async def _mark_done() -> None:
                        done.set()
                    asyncio.run_coroutine_threadsafe(_mark_done(), loop)
            except Exception:
                done.set()

        _ping()
        done.wait(timeout=5.0)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace.flush() error: %s", exc)


def current_session() -> Optional[Session]:
    """
    Return the currently active :class:`Session`, or ``None`` if outside a session.

    Usage::

        with ghostrace.session(name="run") as s:
            sess = ghostrace.current_session()
            assert sess is s

    Returns:
        The innermost open :class:`Session` or ``None``.
    """
    try:
        sid = get_current_session_id()
        if sid is None:
            return None
        return get_session(sid)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace.current_session() error: %s", exc)
        return None

