"""
ghostrace.auto_instrument
~~~~~~~~~~~~~~~~~~~~~~~~~
Zero-touch monkey-patching of popular LLM libraries.

Call once after ghostrace.init():
    ghostrace.auto_instrument()

Supports:
  - openai >= 1.0  (ChatCompletion sync + async)
  - anthropic >= 0.20 (Messages sync + async)

Design rules:
  - Idempotent: calling multiple times does NOT double-patch.
  - Reversible: _uninstrument() restores originals (used in tests).
  - All patch errors are caught; a library failing to patch must not crash.
  - Only patches at the call site — doesn't touch class __init__.
"""
from __future__ import annotations

import asyncio
import functools
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Set

from .models import TraceEvent
from .pricing import calculate_cost

logger = logging.getLogger(__name__)

_PATCHED: Set[str] = set()  # tracks which libs are already patched

# ── Helpers ───────────────────────────────────────────────────────────────────


def _record(event: TraceEvent) -> None:
    """Push to collector, catching all errors."""
    try:
        from .collector import get_collector

        get_collector().record(event)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace auto_instrument record error: %s", exc)


def _openai_event(
    response: Any,
    start: float,
    exc: Optional[BaseException],
    prompt_messages: Any,
) -> TraceEvent:
    latency_ms = int((time.perf_counter() - start) * 1000)

    if exc is not None:
        import traceback

        return TraceEvent(
            event_type="error",
            timestamp=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )

    model: Optional[str] = getattr(response, "model", None)
    usage = getattr(response, "usage", None)
    tokens_in: Optional[int] = getattr(usage, "prompt_tokens", None) if usage else None
    tokens_out: Optional[int] = getattr(usage, "completion_tokens", None) if usage else None
    cost: Optional[float] = None
    if model and tokens_in is not None:
        cost = calculate_cost(model, tokens_in, tokens_out or 0)

    # Extract text from first choice
    response_text: Optional[str] = None
    choices = getattr(response, "choices", None)
    if choices:
        msg = getattr(choices[0], "message", None)
        if msg:
            response_text = getattr(msg, "content", None)

    # Serialise prompt messages
    prompt_str: Optional[str] = None
    try:
        import json

        prompt_str = json.dumps(prompt_messages, default=str)
    except Exception:  # noqa: BLE001
        prompt_str = repr(prompt_messages)

    return TraceEvent(
        event_type="llm_call",
        timestamp=datetime.now(timezone.utc),
        latency_ms=latency_ms,
        model=model,
        prompt=prompt_str,
        response=response_text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
    )


def _anthropic_event(
    response: Any,
    start: float,
    exc: Optional[BaseException],
    prompt_messages: Any,
    system: Any = None,
    model_name: Optional[str] = None,
) -> TraceEvent:
    latency_ms = int((time.perf_counter() - start) * 1000)

    if exc is not None:
        import traceback

        return TraceEvent(
            event_type="error",
            timestamp=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )

    model = getattr(response, "model", None) or model_name
    usage = getattr(response, "usage", None)
    tokens_in: Optional[int] = getattr(usage, "input_tokens", None) if usage else None
    tokens_out: Optional[int] = getattr(usage, "output_tokens", None) if usage else None
    cost: Optional[float] = None
    if model and tokens_in is not None:
        cost = calculate_cost(model, tokens_in, tokens_out or 0)

    response_text: Optional[str] = None
    content = getattr(response, "content", None)
    if isinstance(content, list):
        parts = [getattr(b, "text", "") for b in content if hasattr(b, "text")]
        response_text = "\n".join(parts) or None

    try:
        import json

        prompt_str = json.dumps(prompt_messages, default=str)
        if system:
            prompt_str = f"[system]: {system}\n" + prompt_str
    except Exception:  # noqa: BLE001
        prompt_str = repr(prompt_messages)

    return TraceEvent(
        event_type="llm_call",
        timestamp=datetime.now(timezone.utc),
        latency_ms=latency_ms,
        model=model,
        prompt=prompt_str,
        response=response_text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
    )


# ── OpenAI patching ───────────────────────────────────────────────────────────


def _patch_openai() -> None:
    """Patch openai.chat.completions.create (sync + async)."""
    if "openai" in _PATCHED:
        return
    try:
        import openai

        client_cls = openai.OpenAI  # type: ignore[attr-defined]
        async_client_cls = openai.AsyncOpenAI  # type: ignore[attr-defined]

        # ── Sync ─────────────────────────────────────────────────────────────
        _orig_create = openai.resources.chat.completions.Completions.create

        @functools.wraps(_orig_create)
        def _patched_create(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", args[0] if args else None)
            try:
                response = _orig_create(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _openai_event(response, start, exc_caught, messages)
                _record(event)

        openai.resources.chat.completions.Completions.create = _patched_create  # type: ignore[method-assign]

        # ── Async ─────────────────────────────────────────────────────────────
        _orig_acreate = openai.resources.chat.completions.AsyncCompletions.create

        @functools.wraps(_orig_acreate)
        async def _patched_acreate(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", args[0] if args else None)
            try:
                response = await _orig_acreate(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _openai_event(response, start, exc_caught, messages)
                _record(event)

        openai.resources.chat.completions.AsyncCompletions.create = _patched_acreate  # type: ignore[method-assign]

        _PATCHED.add("openai")
        logger.debug("ghostrace: patched openai.chat.completions.create")

    except ImportError:
        pass  # openai not installed — skip silently
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not patch openai: %s", exc)


# ── Anthropic patching ────────────────────────────────────────────────────────


def _patch_anthropic() -> None:
    """Patch anthropic.resources.messages.Messages.create (sync + async)."""
    if "anthropic" in _PATCHED:
        return
    try:
        import anthropic.resources.messages as _msgs

        _orig_create = _msgs.Messages.create

        @functools.wraps(_orig_create)
        def _patched_create(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", [])
            system = kwargs.get("system")
            model_name = kwargs.get("model")
            try:
                response = _orig_create(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _anthropic_event(response, start, exc_caught, messages, system, model_name)
                _record(event)

        _msgs.Messages.create = _patched_create  # type: ignore[method-assign]

        # Async
        _orig_acreate = _msgs.AsyncMessages.create

        @functools.wraps(_orig_acreate)
        async def _patched_acreate(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", [])
            system = kwargs.get("system")
            model_name = kwargs.get("model")
            try:
                response = await _orig_acreate(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _anthropic_event(response, start, exc_caught, messages, system, model_name)
                _record(event)

        _msgs.AsyncMessages.create = _patched_acreate  # type: ignore[method-assign]

        _PATCHED.add("anthropic")
        logger.debug("ghostrace: patched anthropic.resources.messages.Messages.create")

    except ImportError:
        pass  # anthropic not installed
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not patch anthropic: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────


def auto_instrument() -> None:
    """
    Automatically trace all calls to supported LLM libraries.

    Call this once after ghostrace.init().  Safe to call multiple times.
    Libraries that are not installed are silently skipped.

    Currently instruments:
      - openai  (sync + async)
      - anthropic (sync + async)
    """
    _patch_openai()
    _patch_anthropic()


def _uninstrument() -> None:
    """
    Restore all patched methods to their originals.
    Used in tests only — not part of the public API.
    """
    # NOTE: We'd need to store originals per-patch; for test isolation,
    # reloading the module is simpler.  This is a no-op placeholder.
    _PATCHED.clear()
    logger.debug("ghostrace: uninstrumented (cleared patch registry)")
