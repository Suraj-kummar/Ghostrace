"""
Tests for the @ghostrace.trace decorator.

Covers:
  - Sync function traced → event recorded
  - Async function traced → event recorded
  - Exception in user function → re-raised, error event captured
  - Cost calculated for known model
  - SDK crash inside collector → user function still returns normally
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


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture
def local_config():
    """Init ghostrace in local_only mode (no HTTP)."""
    return init(api_key="gr_test", project="test-project", local_only=True)


# ── Sync decorator tests ──────────────────────────────────────────────────────


class TestSyncDecorator:
    def test_traced_sync_function_returns_value(self, local_config, tmp_path):
        """Decorator must not interfere with the return value."""
        @trace
        def add(a: int, b: int) -> int:
            return a + b

        result = add(2, 3)
        assert result == 5

    def test_sync_event_is_recorded(self, local_config):
        """A trace event must be stored in the collector after the call."""
        recorded: list[TraceEvent] = []

        original_record = get_collector().record

        def capture(event: TraceEvent) -> None:
            recorded.append(event)
            original_record(event)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        def greet(name: str) -> str:
            return f"Hello, {name}"

        greet("World")
        assert len(recorded) == 1
        assert recorded[0].event_type == "llm_call"

    def test_sync_event_captures_latency(self, local_config):
        """latency_ms must be populated and positive."""
        import time

        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        def slow_fn() -> str:
            time.sleep(0.01)
            return "done"

        slow_fn()
        assert recorded[0].latency_ms is not None
        assert recorded[0].latency_ms >= 10  # at least 10 ms

    def test_sync_exception_is_reraised(self, local_config):
        """User exceptions must always propagate through the decorator."""
        @trace
        def boom() -> None:
            raise ValueError("intentional error")

        with pytest.raises(ValueError, match="intentional error"):
            boom()

    def test_sync_exception_creates_error_event(self, local_config):
        """When the function raises, an error event must be captured."""
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        def boom() -> None:
            raise RuntimeError("test error")

        with pytest.raises(RuntimeError):
            boom()

        assert len(recorded) == 1
        assert recorded[0].event_type == "error"
        assert recorded[0].error_type == "RuntimeError"
        assert "test error" in (recorded[0].error_message or "")

    def test_tool_kind_sets_event_type(self, local_config):
        """@trace(kind='tool') must produce a tool_call event."""
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace(kind="tool")
        def fetch_data(url: str) -> dict:
            return {"status": 200}

        fetch_data("https://example.com")
        assert recorded[0].event_type == "tool_call"
        assert recorded[0].tool_name == "fetch_data"

    def test_sdk_crash_does_not_propagate(self, local_config):
        """
        If the collector crashes, the user function must still return normally.
        """
        get_collector().record = MagicMock(side_effect=Exception("SDK CRASH"))

        @trace
        def safe_fn() -> str:
            return "I am safe"

        # Must NOT raise — SDK errors must be silently swallowed
        result = safe_fn()
        assert result == "I am safe"


# ── Async decorator tests ─────────────────────────────────────────────────────


class TestAsyncDecorator:
    async def test_traced_async_function_returns_value(self, local_config):
        @trace
        async def async_add(a: int, b: int) -> int:
            return a + b

        result = await async_add(10, 20)
        assert result == 30

    async def test_async_event_is_recorded(self, local_config):
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        async def async_greet(name: str) -> str:
            return f"Hi, {name}"

        await async_greet("Ghostrace")
        assert len(recorded) == 1
        assert recorded[0].event_type == "llm_call"

    async def test_async_exception_is_reraised(self, local_config):
        @trace
        async def async_boom() -> None:
            raise TypeError("async error")

        with pytest.raises(TypeError, match="async error"):
            await async_boom()

    async def test_async_exception_creates_error_event(self, local_config):
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        async def async_boom() -> None:
            raise ValueError("async boom")

        with pytest.raises(ValueError):
            await async_boom()

        assert recorded[0].event_type == "error"
        assert recorded[0].error_type == "ValueError"

    async def test_async_sdk_crash_does_not_propagate(self, local_config):
        get_collector().record = MagicMock(side_effect=Exception("SDK ASYNC CRASH"))

        @trace
        async def safe_async() -> str:
            return "async safe"

        result = await safe_async()
        assert result == "async safe"


# ── OpenAI response shape auto-extraction ─────────────────────────────────────


class FakeUsage:
    prompt_tokens = 100
    completion_tokens = 50


class FakeMessage:
    content = "The answer is 42."


class FakeChoice:
    message = FakeMessage()


class FakeOpenAIResponse:
    model = "gpt-4o"
    usage = FakeUsage()
    choices = [FakeChoice()]


class TestTokenExtraction:
    def test_tokens_extracted_from_openai_response(self, local_config):
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        def fake_llm(prompt: str) -> Any:
            return FakeOpenAIResponse()

        fake_llm("What is 6*7?")
        event = recorded[0]
        assert event.model == "gpt-4o"
        assert event.tokens_in == 100
        assert event.tokens_out == 50
        assert event.cost_usd is not None
        assert event.cost_usd > 0
        assert event.response == "The answer is 42."

    def test_cost_calculation_is_correct(self, local_config):
        """gpt-4o: in=0.0000025, out=0.000010 per token."""
        recorded: list[TraceEvent] = []
        orig = get_collector().record

        def capture(e: TraceEvent) -> None:
            recorded.append(e)
            orig(e)

        get_collector().record = capture  # type: ignore[method-assign]

        @trace
        def fake_llm(prompt: str) -> Any:
            return FakeOpenAIResponse()  # 100 in, 50 out

        fake_llm("test")
        event = recorded[0]
        # Expected: (100 * 0.0000025) + (50 * 0.000010) = 0.00025 + 0.0005 = 0.00075
        expected = (100 * 0.0000025) + (50 * 0.000010)
        assert event.cost_usd == pytest.approx(expected, rel=1e-6)
