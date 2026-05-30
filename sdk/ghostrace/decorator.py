"""
ghostrace.decorator
~~~~~~~~~~~~~~~~~~~
The @trace decorator — the primary integration point for users.

Usage:
    @ghostrace.trace
    def call_llm(prompt: str) -> str: ...

    @ghostrace.trace(kind="tool")
    def search_web(query: str) -> list: ...

    # Async works identically
    @ghostrace.trace
    async def async_call(prompt: str) -> str: ...

How it works:
  1. Wraps both sync and async callables transparently.
  2. On call: records start time, captures args/kwargs.
  3. On return: captures response, latency_ms, tokens (if present), cost.
  4. On exception: captures error info, re-raises the ORIGINAL exception.
  5. ALL internal errors are swallowed — the user's exception always propagates.

Token / model extraction:
  The decorator inspects the return value for common response shapes from
  openai, anthropic, and other providers.  If found, tokens and model are
  extracted automatically.  Otherwise, the user can pass them via metadata.
"""
from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, TypeVar, Union, overload

from .models import EventType, TraceEvent
from .pricing import calculate_cost

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ── Response introspection helpers ───────────────────────────────────────────


def _extract_model(response: Any) -> Optional[str]:
    """Try to extract model name from a provider response object."""
    if response is None:
        return None
    try:
        # OpenAI / openai-compatible
        if hasattr(response, "model"):
            return str(response.model)
        # Dict responses (some raw API wrappers)
        if isinstance(response, dict):
            return response.get("model")
    except Exception:  # noqa: BLE001
        pass
    return None


def _extract_tokens(response: Any) -> tuple[Optional[int], Optional[int]]:
    """
    Return (tokens_in, tokens_out) from a response object.
    Handles OpenAI and Anthropic response shapes.
    """
    if response is None:
        return None, None
    try:
        # OpenAI: response.usage.prompt_tokens / completion_tokens
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            tokens_in = getattr(usage, "prompt_tokens", None)
            tokens_out = getattr(usage, "completion_tokens", None)
            if tokens_in is not None:
                return int(tokens_in), int(tokens_out or 0)

        # Anthropic: response.usage.input_tokens / output_tokens
        if hasattr(response, "usage") and response.usage:
            usage = response.usage
            tokens_in = getattr(usage, "input_tokens", None)
            tokens_out = getattr(usage, "output_tokens", None)
            if tokens_in is not None:
                return int(tokens_in), int(tokens_out or 0)

        # Dict form
        if isinstance(response, dict) and "usage" in response:
            usage = response["usage"]
            return (
                usage.get("prompt_tokens") or usage.get("input_tokens"),
                usage.get("completion_tokens") or usage.get("output_tokens"),
            )
    except Exception:  # noqa: BLE001
        pass
    return None, None


def _extract_response_text(response: Any) -> Optional[str]:
    """
    Extract the text content from a provider response object.
    Tries openai ChatCompletion, Anthropic Messages, and plain strings.
    """
    if response is None:
        return None
    try:
        if isinstance(response, str):
            return response
        # OpenAI ChatCompletion
        if hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            msg = getattr(choice, "message", None)
            if msg:
                return getattr(msg, "content", None)
            return getattr(choice, "text", None)
        # Anthropic Message
        if hasattr(response, "content") and isinstance(response.content, list):
            parts = [
                getattr(block, "text", "")
                for block in response.content
                if hasattr(block, "text")
            ]
            return "\n".join(parts) or None
        # Fallback: try .content or .text attribute
        if hasattr(response, "content"):
            return str(response.content)
        if hasattr(response, "text"):
            return str(response.text)
    except Exception:  # noqa: BLE001
        pass
    return None


def _serialise_args(args: tuple, kwargs: dict, fn: Callable) -> Optional[str]:
    """
    Build a human-readable string of the function call arguments
    (used as the 'prompt' for generic traces and 'tool_input' for tool traces).
    """
    try:
        sig = inspect.signature(fn)
        bound = sig.bind(*args, **kwargs)
        bound.apply_defaults()
        parts = [f"{k}={v!r}" for k, v in bound.arguments.items()]
        return ", ".join(parts)
    except Exception:  # noqa: BLE001
        return repr(args) if args else None


def _safe_serialise(value: Any) -> Any:
    """Return a JSON-safe version of a value, falling back to str()."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (list, dict)):
        try:
            import json

            json.dumps(value)  # test it
            return value
        except Exception:  # noqa: BLE001
            pass
    try:
        return str(value)
    except Exception:  # noqa: BLE001
        return "<unserializable>"


# ── Core tracing logic ────────────────────────────────────────────────────────


def _build_event(
    fn: Callable,
    args: tuple,
    kwargs: dict,
    kind: EventType,
    start_time: float,
    response: Any = None,
    exc: Optional[BaseException] = None,
) -> TraceEvent:
    """Build a TraceEvent from a completed (or failed) function call."""
    latency_ms = int((time.perf_counter() - start_time) * 1000)
    model = _extract_model(response)
    tokens_in, tokens_out = _extract_tokens(response)
    cost = None
    if model and tokens_in is not None:
        cost = calculate_cost(model, tokens_in, tokens_out or 0)

    if exc is not None:
        return TraceEvent(
            event_type="error",
            timestamp=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            tool_name=fn.__qualname__ if kind == "tool_call" else None,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )

    if kind == "tool_call":
        tool_input_str = _serialise_args(args, kwargs, fn)
        return TraceEvent(
            event_type="tool_call",
            timestamp=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            tool_name=fn.__name__,
            tool_input={"args": tool_input_str} if tool_input_str else None,
            tool_output=_safe_serialise(response),
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=cost,
        )

    # llm_call (default)
    prompt_str = _serialise_args(args, kwargs, fn)
    return TraceEvent(
        event_type="llm_call",
        timestamp=datetime.now(timezone.utc),
        latency_ms=latency_ms,
        model=model,
        prompt=prompt_str,
        response=_extract_response_text(response) or _safe_serialise(response),
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
    )


# ── Public decorator ──────────────────────────────────────────────────────────


@overload
def trace(fn: F) -> F: ...


@overload
def trace(*, kind: str = "llm_call") -> Callable[[F], F]: ...


def trace(
    fn: Optional[Callable] = None,
    *,
    kind: str = "llm_call",
) -> Any:
    """
    Decorator that traces a function call.

    Can be used with or without arguments:
        @trace
        def my_func(): ...

        @trace(kind="tool")
        def my_tool(): ...

    Args:
        kind: "llm_call" (default) | "tool_call" | "custom"
              Controls how the event is displayed in the dashboard.
    """
    # Map user-friendly aliases to canonical event types
    _kind_map: Dict[str, EventType] = {
        "llm_call": "llm_call",
        "llm": "llm_call",
        "tool_call": "tool_call",
        "tool": "tool_call",
        "custom": "custom",
    }
    event_type: EventType = _kind_map.get(kind, "llm_call")

    def decorator(func: F) -> F:
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                exc_caught: Optional[BaseException] = None
                response: Any = None
                try:
                    response = await func(*args, **kwargs)
                    return response
                except Exception as e:
                    exc_caught = e
                    raise
                finally:
                    _record_safe(func, args, kwargs, event_type, start, response, exc_caught)

            return async_wrapper  # type: ignore[return-value]
        else:
            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                exc_caught: Optional[BaseException] = None
                response: Any = None
                try:
                    response = func(*args, **kwargs)
                    return response
                except Exception as e:
                    exc_caught = e
                    raise
                finally:
                    _record_safe(func, args, kwargs, event_type, start, response, exc_caught)

            return sync_wrapper  # type: ignore[return-value]

    # Called as @trace (no parens) — fn is the decorated function directly
    if fn is not None:
        return decorator(fn)

    # Called as @trace(...) — return the decorator
    return decorator


def _record_safe(
    fn: Callable,
    args: tuple,
    kwargs: dict,
    kind: EventType,
    start: float,
    response: Any,
    exc: Optional[BaseException],
) -> None:
    """Build and record the event, catching all SDK-internal errors."""
    try:
        event = _build_event(fn, args, kwargs, kind, start, response, exc)
        from .collector import get_collector

        get_collector().record(event)
    except Exception as sdk_exc:  # noqa: BLE001
        logger.warning("ghostrace: internal error in _record_safe: %s", sdk_exc)
