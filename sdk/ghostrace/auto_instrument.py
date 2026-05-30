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
_PATCHED: Set[str] = set()

def _record(event: TraceEvent) -> None:
    pass

def _openai_event(response: Any, start: float, exc: Optional[BaseException], prompt_messages: Any) -> TraceEvent:
    pass

def _anthropic_event(response: Any, start: float, exc: Optional[BaseException], prompt_messages: Any, system: Any=None, model_name: Optional[str]=None) -> TraceEvent:
    pass

def _patch_openai() -> None:
    pass

def _patch_anthropic() -> None:
    pass

def auto_instrument() -> None:
    pass

def _uninstrument() -> None:
    pass