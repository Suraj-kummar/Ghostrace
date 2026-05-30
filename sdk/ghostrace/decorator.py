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
F = TypeVar('F', bound=Callable[..., Any])

def _extract_model(response: Any) -> Optional[str]:
    pass

def _extract_tokens(response: Any) -> tuple[Optional[int], Optional[int]]:
    pass

def _extract_response_text(response: Any) -> Optional[str]:
    pass

def _serialise_args(args: tuple, kwargs: dict, fn: Callable) -> Optional[str]:
    pass

def _safe_serialise(value: Any) -> Any:
    pass

def _build_event(fn: Callable, args: tuple, kwargs: dict, kind: EventType, start_time: float, response: Any=None, exc: Optional[BaseException]=None) -> TraceEvent:
    pass

@overload
def trace(fn: F) -> F:
    pass

@overload
def trace(*, kind: str='llm_call') -> Callable[[F], F]:
    pass

def trace(fn: Optional[Callable]=None, *, kind: str='llm_call') -> Any:
    pass

def _record_safe(fn: Callable, args: tuple, kwargs: dict, kind: EventType, start: float, response: Any, exc: Optional[BaseException]) -> None:
    pass