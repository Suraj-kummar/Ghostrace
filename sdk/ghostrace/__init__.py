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

    # Zero-touch instrumentation (wraps openai / anthropic automatically)
    ghostrace.auto_instrument()
"""
from __future__ import annotations

from typing import Optional

from .auto_instrument import auto_instrument
from .config import GhostraceConfig, get_config, init
from .decorator import trace
from .session import Session

__version__ = "0.1.0"
__all__ = [
    "init",
    "trace",
    "session",
    "auto_instrument",
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

# Release 0.1.0
