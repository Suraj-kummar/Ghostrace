"""
ghostrace.sender
~~~~~~~~~~~~~~~~
Asynchronous HTTP sender that POSTs trace payloads to the Ghostrace backend.

Behaviour:
  - Batches events and fires them in a background asyncio Task — user code
    is never blocked waiting for a network call.
  - Retries up to 3 times with exponential backoff (1 s → 2 s → 4 s).
  - After all retries are exhausted the payload is handed to the buffer module.
  - On startup (ghostrace.init) replays any files left in the local buffer.
  - All exceptions are caught — this code must never propagate into user code.

Thread safety:
  - Uses asyncio primitives internally.
  - The public method `enqueue` is safe to call from any thread.
"""
from __future__ import annotations
import asyncio
import logging
import threading
from typing import Any, Dict, List, Optional
from .buffer import delete_buffered_file, list_buffered_files, read_buffered_file, write_to_buffer
from .config import get_config
logger = logging.getLogger(__name__)
_RETRY_DELAYS = (1.0, 2.0, 4.0)

class HttpSender:
    """
    Manages an internal asyncio event loop (in a daemon thread) to send
    events without blocking the caller's thread or event loop.
    """

    def __init__(self) -> None:
        pass

    def start(self) -> None:
        pass

    def _run_loop(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def enqueue(self, payload: Dict[str, Any]) -> None:
        pass

    def replay_buffer(self) -> None:
        pass

    async def _worker(self) -> None:
        pass

    async def _send_with_retry(self, client: Any, payload: Dict[str, Any]) -> None:
        pass

    @staticmethod
    def _make_client() -> Any:
        pass
_sender: Optional[HttpSender] = None

def get_sender() -> HttpSender:
    pass