"""
Tests for the HTTP sender (HttpSender) using respx to mock HTTP calls.

Covers:
  - Successful send → no buffer file created
  - 3 consecutive failures → event written to buffer
  - 429 response → no buffer (user must upgrade)
  - Retry backoff sequence is triggered on failure
"""
from __future__ import annotations

import json
import asyncio
import threading
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghostrace.config import init
from ghostrace.models import SessionPayload, TraceEvent
from ghostrace.sender import HttpSender


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_payload() -> dict:
    event = TraceEvent(event_type="llm_call", model="gpt-4o")
    payload = SessionPayload(
        session_id="test-session-id",
        project="test-project",
        events=[event],
    )
    return payload.to_dict()


# ── Tests ──────────────────────────────────────────────────────────────────────


class TestHttpSender:
    """
    We test the _send_with_retry coroutine directly to avoid threading
    complexity in unit tests.

    IMPORTANT: patch targets use "ghostrace.sender.write_to_buffer" (not
    "ghostrace.buffer.write_to_buffer") because sender.py imports the function
    via `from .buffer import write_to_buffer`, binding it in the sender module's
    own namespace.  Patching the origin module would not intercept that binding.
    """

    @pytest.fixture
    def sender(self):
        init(api_key="gr_test", project="test-project")
        s = HttpSender()
        return s

    async def test_successful_send_does_not_write_buffer(self, sender, tmp_path):
        """HTTP 200 → buffer must NOT be written."""
        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("ghostrace.sender.write_to_buffer") as mock_buffer:
            await sender._send_with_retry(mock_client, _make_payload())

        mock_buffer.assert_not_called()
        mock_client.post.assert_called_once()

    async def test_three_failures_writes_to_buffer(self, sender):
        """Three consecutive HTTP errors → write_to_buffer must be called once."""
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("connection refused"))

        with patch("ghostrace.sender.write_to_buffer") as mock_buffer:
            with patch("asyncio.sleep", new_callable=AsyncMock):  # skip actual delays
                await sender._send_with_retry(mock_client, _make_payload())

        mock_buffer.assert_called_once()
        # Verify the buffered payload contains our session_id
        buffered_arg = mock_buffer.call_args[0][0]
        assert buffered_arg["session_id"] == "test-session-id"

    async def test_http_500_retries_then_buffers(self, sender):
        """HTTP 500 should trigger retries and finally buffer."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("ghostrace.sender.write_to_buffer") as mock_buffer:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await sender._send_with_retry(mock_client, _make_payload())

        # Should have tried 3 times
        assert mock_client.post.call_count == 3
        # Should have written to buffer
        mock_buffer.assert_called_once()

    async def test_429_does_not_write_to_buffer(self, sender):
        """HTTP 429 (trace limit) should log but NOT buffer."""
        mock_response = MagicMock()
        mock_response.status_code = 429

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("ghostrace.sender.write_to_buffer") as mock_buffer:
            await sender._send_with_retry(mock_client, _make_payload())

        mock_buffer.assert_not_called()
        # Only one attempt for 429 (no point retrying an upgrade-required response)
        mock_client.post.assert_called_once()

    async def test_success_after_first_retry(self, sender):
        """First call fails, second succeeds → buffer NOT called."""
        fail_response = MagicMock()
        fail_response.status_code = 503

        ok_response = MagicMock()
        ok_response.status_code = 200

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=[fail_response, ok_response])

        with patch("ghostrace.sender.write_to_buffer") as mock_buffer:
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await sender._send_with_retry(mock_client, _make_payload())

        mock_buffer.assert_not_called()
        assert mock_client.post.call_count == 2

    async def test_replay_buffer_file_deleted_on_success(self, sender, tmp_path):
        """When replaying a buffered file, it should be deleted on success."""
        buf_file = tmp_path / "test-buffer.json"
        buf_file.write_text("{}")

        payload = _make_payload()
        payload["_buffered_path"] = str(buf_file)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)

        with patch("ghostrace.sender.delete_buffered_file") as mock_delete:
            await sender._send_with_retry(mock_client, payload)

        mock_delete.assert_called_once_with(Path(str(buf_file)))

# Boundary tests for timeout and transmission failures
