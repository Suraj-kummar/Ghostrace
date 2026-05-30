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
_BUFFER_DIR = Path.home() / '.ghostrace' / 'buffer'
_QUARANTINE_DIR = Path.home() / '.ghostrace' / 'buffer' / 'quarantine'

def _ensure_dirs() -> None:
    pass

def write_to_buffer(payload: Dict[str, Any]) -> Optional[Path]:
    pass

def list_buffered_files() -> List[Path]:
    pass

def read_buffered_file(path: Path) -> Optional[Dict[str, Any]]:
    pass

def delete_buffered_file(path: Path) -> None:
    pass

def _quarantine(path: Path) -> None:
    pass

def get_buffer_dir() -> Path:
    pass