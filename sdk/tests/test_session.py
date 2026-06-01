"""
Tests for ghostrace.session context manager.

Covers:
  - Events inside a session get the correct session_id
  - Tags are attached to the session
  - Nested sessions: innermost session wins
  - Async session context manager
  - Session duration_ms is populated after exit
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import ghostrace
from ghostrace.collector import get_collector
from ghostrace.config import init
from ghostrace.decorator import trace
from ghostrace.models import TraceEvent
from ghostrace.session import Session, get_current_session_id


@pytest.fixture
def local_config():
    return init(api_key="gr_test", project="test-project", local_only=True)


class TestSyncSession:
    def test_session_assigns_id_to_events(self, local_config):
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        def fn() -> str:
            return "ok"

        with ghostrace.session(name="test-session") as s:
            fn()

        assert len(recorded) == 1
        assert recorded[0].session_id == s.id

    def test_tags_are_stored(self, local_config):
        with ghostrace.session() as s:
            s.tag("user_id", "u_42")
            s.tag("env", "test")

        assert s.tags == {"user_id": "u_42", "env": "test"}

    def test_tag_is_chainable(self, local_config):
        with ghostrace.session() as s:
            result = s.tag("k", "v")
        assert result is s

    def test_session_duration_set_on_exit(self, local_config):
        import time

        with ghostrace.session() as s:
            time.sleep(0.01)

        assert s.duration_ms() is not None
        assert s.duration_ms() >= 10  # type: ignore[operator]

    def test_no_session_outside_context(self, local_config):
        """get_current_session_id() must return None outside a session block."""
        assert get_current_session_id() is None

    def test_session_id_cleared_after_exit(self, local_config):
        with ghostrace.session() as s:
            inside_id = get_current_session_id()
        outside_id = get_current_session_id()

        assert inside_id == s.id
        assert outside_id is None

    def test_nested_sessions_innermost_wins(self, local_config):
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        def inner_fn() -> str:
            return "inner"

        @trace
        def outer_fn() -> str:
            return "outer"

        with ghostrace.session(name="outer") as outer:
            outer_fn()  # should attach to outer
            with ghostrace.session(name="inner") as inner:
                inner_fn()  # should attach to inner

        assert recorded[0].session_id == outer.id  # outer_fn
        assert recorded[1].session_id == inner.id  # inner_fn

    def test_explicit_session_id_is_used(self, local_config):
        custom_id = "my-custom-session-id"
        with ghostrace.session(session_id=custom_id) as s:
            pass
        assert s.id == custom_id

    def test_exception_in_session_does_not_swallow(self, local_config):
        with pytest.raises(RuntimeError, match="agent exploded"):
            with ghostrace.session() as s:
                raise RuntimeError("agent exploded")

        # Session should still be closed
        assert s.ended_at is not None


class TestAsyncSession:
    async def test_async_session_assigns_id(self, local_config):
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        async def async_fn() -> str:
            return "async ok"

        async with ghostrace.session(name="async-session") as s:
            await async_fn()

        assert len(recorded) == 1
        assert recorded[0].session_id == s.id

    async def test_async_session_tags(self, local_config):
        async with ghostrace.session() as s:
            s.tag("framework", "asyncio")

        assert s.tags == {"framework": "asyncio"}
