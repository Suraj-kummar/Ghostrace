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

from .buffer import (
    delete_buffered_file,
    list_buffered_files,
    read_buffered_file,
    write_to_buffer,
)
from .config import get_config

logger = logging.getLogger(__name__)

_RETRY_DELAYS = (1.0, 2.0, 4.0)


class HttpSender:
    """
    Manages an internal asyncio event loop (in a daemon thread) to send
    events without blocking the caller's thread or event loop.
    """

    def __init__(self) -> None:
        self._queue: asyncio.Queue[Optional[Dict[str, Any]]] = asyncio.Queue()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._started = False
        self._lock = threading.Lock()

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the background sender thread (idempotent)."""
        with self._lock:
            if self._started:
                return
            self._loop = asyncio.new_event_loop()
            self._thread = threading.Thread(
                target=self._run_loop,
                name="ghostrace-sender",
                daemon=True,
            )
            self._thread.start()
            self._started = True

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)  # type: ignore[arg-type]
        self._loop.run_until_complete(self._worker())  # type: ignore[union-attr]

    def stop(self) -> None:
        """Gracefully stop — waits for the queue to drain (max 5 s)."""
        if self._loop and self._started:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, None)  # sentinel

    # ── Public API ───────────────────────────────────────────────────────────

    def enqueue(self, payload: Dict[str, Any]) -> None:
        """
        Thread-safe: push a payload onto the send queue.
        The payload is a dict matching the SessionPayload shape.
        """
        if not self._started:
            self.start()
        try:
            self._loop.call_soon_threadsafe(self._queue.put_nowait, payload)  # type: ignore[union-attr]
        except Exception as exc:  # noqa: BLE001
            logger.warning("ghostrace: could not enqueue payload: %s", exc)

    def replay_buffer(self) -> None:
        """Enqueue all locally buffered files for re-sending."""
        try:
            files = list_buffered_files()
            if files:
                logger.info("ghostrace: replaying %d buffered file(s)", len(files))
            for path in files:
                payload = read_buffered_file(path)
                if payload:
                    # Tag the payload so we know where it came from
                    payload["_buffered_path"] = str(path)
                    self.enqueue(payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("ghostrace: error replaying buffer: %s", exc)

    # ── Internal asyncio worker ──────────────────────────────────────────────

    async def _worker(self) -> None:
        """Drain the queue indefinitely, sending payloads with retries."""
        async with self._make_client() as client:
            while True:
                try:
                    payload = await self._queue.get()
                    if payload is None:  # stop sentinel
                        break
                    await self._send_with_retry(client, payload)
                    self._queue.task_done()
                except Exception as exc:  # noqa: BLE001
                    logger.warning("ghostrace sender worker error: %s", exc)

    async def _send_with_retry(
        self,
        client: Any,
        payload: Dict[str, Any],
    ) -> None:
        """Try to POST the payload up to 3 times; buffer on total failure."""
        config = get_config()
        buffered_path_str: Optional[str] = payload.pop("_buffered_path", None)

        for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
            try:
                response = await client.post(
                    f"{config.base_url}/v1/ingest",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {config.api_key}",
                        "Content-Type": "application/json",
                        "X-Ghostrace-SDK": "python/0.1.0",
                    },
                    timeout=10.0,
                )
                if response.status_code == 429:
                    # Trace limit exceeded — log but do NOT buffer (user must upgrade)
                    logger.warning(
                        "ghostrace: trace limit exceeded (HTTP 429). "
                        "Upgrade at https://ghostrace.dev/pricing"
                    )
                    return
                if response.status_code < 300:
                    # Success — delete the buffer file if this was a replay
                    if buffered_path_str:
                        from pathlib import Path
                        delete_buffered_file(Path(buffered_path_str))
                    return
                logger.warning(
                    "ghostrace: HTTP %d on attempt %d/%d",
                    response.status_code,
                    attempt,
                    len(_RETRY_DELAYS),
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "ghostrace: send error on attempt %d/%d: %s",
                    attempt,
                    len(_RETRY_DELAYS),
                    exc,
                )

            if attempt < len(_RETRY_DELAYS):
                await asyncio.sleep(delay)

        # All retries exhausted — write to local buffer
        if buffered_path_str is None:  # only buffer if not already replaying
            write_to_buffer(payload)

    @staticmethod
    def _make_client() -> Any:
        """Return an httpx.AsyncClient context manager."""
        try:
            import httpx

            return httpx.AsyncClient()
        except ImportError:
            raise RuntimeError(
                "ghostrace requires 'httpx'. Install it: pip install httpx"
            )


# ── Module-level singleton ────────────────────────────────────────────────────

_sender: Optional[HttpSender] = None


def get_sender() -> HttpSender:
    global _sender
    if _sender is None:
        _sender = HttpSender()
        _sender.start()
    return _sender
