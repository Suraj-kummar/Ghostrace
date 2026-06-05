"""
tests.test_public_api
~~~~~~~~~~~~~~~~~~~~~
Tests for the new module-level convenience functions:
  - ghostrace.tag()
  - ghostrace.flush()
  - ghostrace.current_session()
"""
from __future__ import annotations

from unittest.mock import patch

import pytest

import ghostrace
from ghostrace.auto_instrument import _uninstrument
from ghostrace.collector import get_collector


@pytest.fixture(autouse=True)
def _reset(tmp_path):
    ghostrace.init(local_only=True, project="test-public-api")
    _uninstrument()
    c = get_collector()
    with c._lock:
        c._sessions.clear()
        c._seq.clear()
    with patch("ghostrace.writer.write_event"):
        yield
    with c._lock:
        c._sessions.clear()
        c._seq.clear()


# ── ghostrace.current_session() ──────────────────────────────────────────────


class TestCurrentSession:
    def test_returns_none_outside_session(self):
        assert ghostrace.current_session() is None

    def test_returns_session_inside_context(self):
        with ghostrace.session(name="my-run") as s:
            result = ghostrace.current_session()
            assert result is s
            assert result.name == "my-run"

    def test_returns_none_after_session_exits(self):
        with ghostrace.session(name="done") as s:
            pass
        assert ghostrace.current_session() is None

    def test_nested_sessions_return_innermost(self):
        with ghostrace.session(name="outer") as outer:
            with ghostrace.session(name="inner") as inner:
                assert ghostrace.current_session() is inner
            # back to outer after inner exits
            assert ghostrace.current_session() is outer

    @pytest.mark.asyncio
    async def test_returns_session_in_async_context(self):
        async with ghostrace.session(name="async-run") as s:
            result = ghostrace.current_session()
            assert result is s


# ── ghostrace.tag() ───────────────────────────────────────────────────────────


class TestModuleLevelTag:
    def test_tag_inside_session(self):
        with ghostrace.session(name="tag-test") as s:
            ghostrace.tag("env", "staging")
            ghostrace.tag("user_id", "u_42")

        assert s.tags["env"] == "staging"
        assert s.tags["user_id"] == "u_42"

    def test_tag_outside_session_does_not_raise(self):
        # Should silently ignore when no session is active
        ghostrace.tag("key", "value")   # no error

    def test_tag_is_chainable_via_session(self):
        with ghostrace.session(name="chain") as s:
            s.tag("a", "1").tag("b", "2")
            assert s.tags == {"a": "1", "b": "2"}

    def test_tag_appended_to_correct_session(self):
        with ghostrace.session(name="outer") as outer:
            ghostrace.tag("scope", "outer")
            with ghostrace.session(name="inner") as inner:
                ghostrace.tag("scope", "inner")
            # Outer session should still have its own tag unchanged
            assert outer.tags["scope"] == "outer"
            assert inner.tags["scope"] == "inner"

    def test_tag_value_is_coerced_to_str(self):
        with ghostrace.session(name="coerce") as s:
            s.tag("count", 42)  # type: ignore[arg-type]  — Session.tag does str()
        assert s.tags["count"] == "42"

    @pytest.mark.asyncio
    async def test_tag_inside_async_session(self):
        async with ghostrace.session(name="async-tag") as s:
            ghostrace.tag("framework", "asyncio")
        assert s.tags["framework"] == "asyncio"


# ── ghostrace.flush() ─────────────────────────────────────────────────────────


class TestFlush:
    def test_flush_does_not_raise(self):
        """flush() must never propagate exceptions into user code."""
        ghostrace.flush()  # no crash even with no sender started

    def test_flush_returns_none(self):
        result = ghostrace.flush()
        assert result is None

    def test_flush_is_safe_to_call_multiple_times(self):
        ghostrace.flush()
        ghostrace.flush()
        ghostrace.flush()

    def test_flush_is_safe_before_init(self):
        """Reset config to simulate calling flush before init."""
        import ghostrace.config as _cfg
        original = _cfg._INSTANCE
        _cfg._INSTANCE = None
        try:
            ghostrace.flush()  # must not raise
        finally:
            _cfg._INSTANCE = original


# ── Version check ──────────────────────────────────────────────────────────────


def test_version_is_0_2_0():
    assert ghostrace.__version__ == "0.2.0"


def test_all_exports_present():
    expected = {"init", "trace", "session", "auto_instrument",
                "tag", "flush", "current_session",
                "get_config", "GhostraceConfig", "Session", "__version__"}
    missing = expected - set(ghostrace.__all__)
    assert not missing, f"Missing from __all__: {missing}"
