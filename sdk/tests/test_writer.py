"""
Tests for ghostrace.writer — local NDJSON trace output.

Covers:
  - Events are written to the correct path
  - File is valid NDJSON (one JSON per line)
  - Multiple events accumulate in the same file
  - Permission error is caught silently
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

import pytest

import ghostrace.writer as writer_module
from ghostrace.models import TraceEvent
from ghostrace.writer import write_event


@pytest.fixture
def isolated_writer(tmp_path, monkeypatch):
    traces_dir = tmp_path / "traces"
    monkeypatch.setattr(writer_module, "_TRACES_DIR", traces_dir)
    return traces_dir


class TestWriteEvent:
    def test_creates_ndjson_file(self, isolated_writer):
        event = TraceEvent(event_type="llm_call", model="gpt-4o")
        write_event(event.to_dict())
        files = list(isolated_writer.glob("*.ndjson"))
        assert len(files) == 1

    def test_written_line_is_valid_json(self, isolated_writer):
        event = TraceEvent(
            event_type="llm_call",
            model="gpt-4o",
            tokens_in=100,
            tokens_out=50,
        )
        write_event(event.to_dict())
        files = list(isolated_writer.glob("*.ndjson"))
        line = files[0].read_text().strip()
        parsed = json.loads(line)
        assert parsed["event_type"] == "llm_call"
        assert parsed["model"] == "gpt-4o"
        assert parsed["tokens_in"] == 100

    def test_multiple_events_append(self, isolated_writer):
        for i in range(5):
            event = TraceEvent(event_type="custom", metadata={"i": i})
            write_event(event.to_dict())
        files = list(isolated_writer.glob("*.ndjson"))
        lines = files[0].read_text().strip().split("\n")
        assert len(lines) == 5

    def test_permission_error_does_not_raise(self, isolated_writer):
        """Writer must swallow filesystem errors silently."""
        with patch("builtins.open", side_effect=PermissionError("no write")):
            # Must NOT raise
            write_event({"event_type": "custom"})

    def test_filename_is_todays_date(self, isolated_writer):
        event = TraceEvent(event_type="custom")
        write_event(event.to_dict())
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        files = list(isolated_writer.glob("*.ndjson"))
        assert files[0].stem == today

    def test_tool_event_fields_preserved(self, isolated_writer):
        event = TraceEvent(
            event_type="tool_call",
            tool_name="search_web",
            tool_input={"query": "AI news"},
            tool_output={"results": ["item1"]},
        )
        write_event(event.to_dict())
        files = list(isolated_writer.glob("*.ndjson"))
        parsed = json.loads(files[0].read_text().strip())
        assert parsed["tool_name"] == "search_web"
        assert parsed["tool_input"]["query"] == "AI news"

    def test_error_event_fields_preserved(self, isolated_writer):
        event = TraceEvent(
            event_type="error",
            error_type="ValueError",
            error_message="bad input",
            stack_trace="Traceback...",
        )
        write_event(event.to_dict())
        files = list(isolated_writer.glob("*.ndjson"))
        parsed = json.loads(files[0].read_text().strip())
        assert parsed["error_type"] == "ValueError"
        assert parsed["error_message"] == "bad input"
