"""
Tests for ghostrace.buffer — offline event buffering.

Covers:
  - write_to_buffer creates an atomic file
  - list_buffered_files returns files in order
  - read_buffered_file parses correctly
  - Corrupt file is quarantined, not raised
  - delete_buffered_file removes the file
"""
from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

import ghostrace.buffer as buf_module
from ghostrace.buffer import (
    delete_buffered_file,
    list_buffered_files,
    read_buffered_file,
    write_to_buffer,
)


@pytest.fixture
def isolated_buffer(tmp_path, monkeypatch):
    """Redirect buffer dirs to a temp directory."""
    buffer_dir = tmp_path / "buffer"
    quarantine_dir = buffer_dir / "quarantine"
    buffer_dir.mkdir()
    quarantine_dir.mkdir()
    monkeypatch.setattr(buf_module, "_BUFFER_DIR", buffer_dir)
    monkeypatch.setattr(buf_module, "_QUARANTINE_DIR", quarantine_dir)
    return buffer_dir, quarantine_dir


class TestWriteToBuffer:
    def test_creates_json_file(self, isolated_buffer):
        buffer_dir, _ = isolated_buffer
        payload = {"session_id": "abc", "events": [{"type": "llm_call"}]}
        path = write_to_buffer(payload)
        assert path is not None
        assert path.exists()
        assert path.suffix == ".json"

    def test_file_is_valid_json(self, isolated_buffer):
        write_to_buffer({"key": "value"})
        files = list_buffered_files()
        assert len(files) == 1
        with open(files[0]) as f:
            data = json.load(f)
        assert data["key"] == "value"

    def test_atomic_write(self, isolated_buffer):
        """No .tmp files should remain after write."""
        buffer_dir, _ = isolated_buffer
        write_to_buffer({"x": 1})
        tmp_files = list(buffer_dir.glob(".tmp-*"))
        assert len(tmp_files) == 0


class TestListBufferedFiles:
    def test_returns_empty_when_no_files(self, isolated_buffer):
        assert list_buffered_files() == []

    def test_returns_files_sorted_oldest_first(self, isolated_buffer):
        # Write two files with a tiny gap
        p1 = write_to_buffer({"order": 1})
        time.sleep(0.01)
        p2 = write_to_buffer({"order": 2})
        files = list_buffered_files()
        assert len(files) == 2
        assert files[0] == p1
        assert files[1] == p2


class TestReadBufferedFile:
    def test_reads_valid_file(self, isolated_buffer):
        payload = {"session_id": "xyz", "events": []}
        path = write_to_buffer(payload)
        result = read_buffered_file(path)  # type: ignore[arg-type]
        assert result is not None
        assert result["session_id"] == "xyz"

    def test_corrupt_file_is_quarantined(self, isolated_buffer):
        buffer_dir, quarantine_dir = isolated_buffer
        corrupt = buffer_dir / "corrupt.json"
        corrupt.write_text("THIS IS NOT JSON {{{")
        result = read_buffered_file(corrupt)
        assert result is None
        # File should be moved to quarantine
        assert not corrupt.exists()
        assert (quarantine_dir / "corrupt.json").exists()


class TestDeleteBufferedFile:
    def test_deletes_file(self, isolated_buffer):
        path = write_to_buffer({"del": True})
        assert path is not None
        assert path.exists()
        delete_buffered_file(path)
        assert not path.exists()

    def test_does_not_raise_if_missing(self, isolated_buffer):
        fake = Path("/tmp/ghostrace-does-not-exist.json")
        # Must not raise
        delete_buffered_file(fake)
