"""
ghostrace.buffer
~~~~~~~~~~~~~~~~
Offline event buffer.

When the HTTP send fails after all retries, events are written atomically
to ~/.ghostrace/buffer/<timestamp>-<uuid>.json.  On the next ghostrace.init()
call, buffered files are replayed through the sender.

Design goals:
  - Atomic writes (temp file → rename) — no partial files
  - Never raises into user code
  - Replay is best-effort — corrupt files are quarantined, not retried forever
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_BUFFER_DIR = Path.home() / ".ghostrace" / "buffer"
_QUARANTINE_DIR = Path.home() / ".ghostrace" / "buffer" / "quarantine"


def _ensure_dirs() -> None:
    try:
        _BUFFER_DIR.mkdir(parents=True, exist_ok=True)
        _QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not create buffer dirs: %s", exc)


def write_to_buffer(payload: Dict[str, Any]) -> Optional[Path]:
    """
    Atomically write a payload dict to the buffer directory.

    Returns the path written, or None if writing failed.
    """
    _ensure_dirs()
    try:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        uid = uuid.uuid4().hex[:8]
        filename = f"{timestamp}-{uid}.json"
        final_path = _BUFFER_DIR / filename
        tmp_path = _BUFFER_DIR / f".tmp-{filename}"

        with open(tmp_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, default=str)

        tmp_path.rename(final_path)
        logger.warning(
            "ghostrace: backend unreachable — buffered %d events to %s",
            len(payload.get("events", [])),
            final_path,
        )
        return final_path
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not write to buffer: %s", exc)
        return None


def list_buffered_files() -> List[Path]:
    """Return all pending buffer files sorted oldest-first."""
    _ensure_dirs()
    try:
        return sorted(
            (
                p
                for p in _BUFFER_DIR.iterdir()
                if p.is_file() and p.suffix == ".json"
            ),
            key=lambda p: p.stat().st_mtime,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not list buffer dir: %s", exc)
        return []


def read_buffered_file(path: Path) -> Optional[Dict[str, Any]]:
    """Read and parse a buffered file; return None if corrupt."""
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: corrupt buffer file %s (%s) — quarantining", path, exc)
        _quarantine(path)
        return None


def delete_buffered_file(path: Path) -> None:
    """Delete a successfully replayed buffer file."""
    try:
        path.unlink(missing_ok=True)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not delete buffer file %s: %s", path, exc)


def _quarantine(path: Path) -> None:
    """Move a corrupt file away so it isn't retried."""
    try:
        dest = _QUARANTINE_DIR / path.name
        shutil.move(str(path), dest)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not quarantine %s: %s", path, exc)


def get_buffer_dir() -> Path:
    return _BUFFER_DIR
