"""
ghostrace.writer
~~~~~~~~~~~~~~~~
Writes trace events to a local NDJSON file at:
    ~/.ghostrace/traces/<YYYY-MM-DD>.ndjson

One JSON object per line (newline-delimited JSON).  This gives the user
a local audit trail even when the backend is unreachable, and lets them
grep/jq their own traces without the dashboard.

All filesystem errors are caught silently — the writer must never
propagate an exception into user code.
"""
from __future__ import annotations
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
logger = logging.getLogger(__name__)
_TRACES_DIR = Path.home() / '.ghostrace' / 'traces'

def _ensure_dir() -> Path:
    pass

def _today_path() -> Path:
    pass

def write_event(event_dict: Dict[str, Any]) -> None:
    pass

def get_trace_dir() -> Path:
    pass