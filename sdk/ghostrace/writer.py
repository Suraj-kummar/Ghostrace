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

_TRACES_DIR = Path.home() / ".ghostrace" / "traces"


def _ensure_dir() -> Path:
    """Create the traces directory if it doesn't exist; return its path."""
    try:
        _TRACES_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not create traces dir: %s", exc)
    return _TRACES_DIR


def _today_path() -> Path:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return _ensure_dir() / f"{date_str}.ndjson"


def write_event(event_dict: Dict[str, Any]) -> None:
    """
    Append a single trace event to today's NDJSON file.

    This is a synchronous, thread-safe append — file opens are short-lived
    and the OS guarantees atomic appends at the block level on all major FSes.

    Args:
        event_dict: A JSON-serialisable dict (from TraceEvent.to_dict()).
    """
    try:
        line = json.dumps(event_dict, default=str) + "\n"
        path = _today_path()
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
        if os.environ.get("GHOSTRACE_DEBUG"):
            logger.debug("ghostrace: wrote event %s to %s", event_dict.get("id"), path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: failed to write local trace: %s", exc)


def get_trace_dir() -> Path:
    """Return the path to the local traces directory."""
    return _TRACES_DIR
