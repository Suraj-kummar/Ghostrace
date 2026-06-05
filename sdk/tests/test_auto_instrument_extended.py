"""
tests.test_auto_instrument_extended
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for LangChain, LlamaIndex, and Google Generative AI auto-instrumentation.

All external libraries are faked with lightweight stubs so these tests run
without installing langchain / llama-index / google-generativeai.
"""
from __future__ import annotations

import sys
import types
from typing import Any, Optional
from unittest.mock import MagicMock, patch

import pytest

import ghostrace
from ghostrace.auto_instrument import _PATCHED, _uninstrument
from ghostrace.collector import get_collector
from ghostrace.models import TraceEvent


# ── Helpers ───────────────────────────────────────────────────────────────────


def _collected_events() -> list[TraceEvent]:
    """Return all events currently buffered in the collector (any session)."""
    c = get_collector()
    all_events: list[TraceEvent] = []
    with c._lock:
        for events in c._sessions.values():
            all_events.extend(events)
    return all_events


def _all_recorded_events(mock_write) -> list[dict]:
    """
    Return all events passed to write_event() mock.
    This catches both buffered and immediately-sent events.
    """
    return [call.args[0] for call in mock_write.call_args_list]


def _reset_collector() -> None:
    """Wipe collector state between tests."""
    c = get_collector()
    with c._lock:
        c._sessions.clear()
        c._seq.clear()


@pytest.fixture(autouse=True)
def _setup(tmp_path):
    """Reset SDK state before every test."""
    ghostrace.init(local_only=True, project="test")
    _uninstrument()
    _reset_collector()

    with patch("ghostrace.writer.write_event") as mock_write:
        yield mock_write

    _uninstrument()
    _reset_collector()


# ── LangChain stubs ───────────────────────────────────────────────────────────


def _make_langchain_stub():
    """
    Inject minimal langchain_core stub modules into sys.modules so that
    _patch_langchain() can import them without the real package installed.
    """
    # Build stub module tree
    lc_core = types.ModuleType("langchain_core")
    lc_lm = types.ModuleType("langchain_core.language_models")
    lc_chat = types.ModuleType("langchain_core.language_models.chat_models")
    lc_llms = types.ModuleType("langchain_core.language_models.llms")
    lc_msgs = types.ModuleType("langchain_core.messages")

    class _FakeChatResult:
        def __init__(self, text: str, model: str, tokens_in: int, tokens_out: int):
            self.generations = [[_FakeGen(text)]]
            self.llm_output = {
                "token_usage": {"prompt_tokens": tokens_in, "completion_tokens": tokens_out},
                "model_name": model,
            }

    class _FakeGen:
        def __init__(self, text: str):
            self.text = text

    class BaseChatModel:
        model_name = "gpt-4o"

        def _generate(self, messages, *args, **kwargs):  # original
            return _FakeChatResult("hello from chat", self.model_name, 10, 5)

        async def _agenerate(self, messages, *args, **kwargs):
            return _FakeChatResult("async hello", self.model_name, 8, 4)

    class BaseLLM:
        model_name = "gpt-3.5-turbo"

        def _generate(self, prompts, *args, **kwargs):
            result = _FakeChatResult("llm result", self.model_name, 20, 10)
            return result

    class BaseMessage:
        def __init__(self, content: str):
            self.content = content

    lc_chat.BaseChatModel = BaseChatModel
    lc_llms.BaseLLM = BaseLLM
    lc_msgs.BaseMessage = BaseMessage

    lc_core.language_models = lc_lm
    lc_lm.chat_models = lc_chat
    lc_lm.llms = lc_llms

    for name, mod in [
        ("langchain_core", lc_core),
        ("langchain_core.language_models", lc_lm),
        ("langchain_core.language_models.chat_models", lc_chat),
        ("langchain_core.language_models.llms", lc_llms),
        ("langchain_core.messages", lc_msgs),
    ]:
        sys.modules.setdefault(name, mod)

    return BaseChatModel, BaseLLM, BaseMessage, _FakeChatResult


def _cleanup_langchain_stub():
    for name in [
        "langchain_core",
        "langchain_core.language_models",
        "langchain_core.language_models.chat_models",
        "langchain_core.language_models.llms",
        "langchain_core.messages",
    ]:
        sys.modules.pop(name, None)


# ── LangChain tests ───────────────────────────────────────────────────────────


class TestLangChainPatch:
    def setup_method(self):
        self.BaseChatModel, self.BaseLLM, _, _ = _make_langchain_stub()

    def teardown_method(self):
        _uninstrument()
        _cleanup_langchain_stub()

    def test_patch_langchain_is_idempotent(self):
        from ghostrace.auto_instrument import _patch_langchain
        _patch_langchain()
        _patch_langchain()  # second call should be a no-op
        assert "langchain" in _PATCHED

    def test_chat_model_generate_records_event(self):
        from ghostrace.auto_instrument import _patch_langchain
        _patch_langchain()

        model = self.BaseChatModel()
        from langchain_core.messages import BaseMessage
        msgs = [BaseMessage("Hello")]
        model._generate(msgs)

        events = _collected_events()
        assert len(events) == 1
        ev = events[0]
        assert ev.event_type == "llm_call"
        assert ev.model == "gpt-4o"
        assert ev.response == "hello from chat"
        assert ev.tokens_in == 10
        assert ev.tokens_out == 5
        assert ev.latency_ms is not None and ev.latency_ms >= 0

    def test_chat_model_generate_records_error(self, _setup):
        from ghostrace.auto_instrument import _patch_langchain

        # Make the stub raise BEFORE patching so the closure captures it
        def _raising_generate(self_inner, messages, *args, **kwargs):
            raise ValueError("boom")

        self.BaseChatModel._generate = _raising_generate
        _patch_langchain()

        model = self.BaseChatModel()
        with pytest.raises(ValueError):
            model._generate([])

        written = _collected_events()
        assert any(
            e.event_type == "error" and e.error_type == "ValueError"
            for e in written
        )

    @pytest.mark.asyncio
    async def test_chat_model_agenerate_records_event(self):
        from ghostrace.auto_instrument import _patch_langchain
        _patch_langchain()

        model = self.BaseChatModel()
        from langchain_core.messages import BaseMessage
        msgs = [BaseMessage("Hi async")]
        await model._agenerate(msgs)

        events = _collected_events()
        assert any(e.event_type == "llm_call" and e.response == "async hello" for e in events)

    def test_base_llm_generate_records_event(self):
        from ghostrace.auto_instrument import _patch_langchain
        _patch_langchain()

        model = self.BaseLLM()
        model._generate(["What is Python?"])

        events = _collected_events()
        assert any(e.event_type == "llm_call" and e.prompt == "What is Python?" for e in events)


# ── LlamaIndex stubs + tests ─────────────────────────────────────────────────


def _make_llama_index_stub():
    li_core = types.ModuleType("llama_index")
    li_core_sub = types.ModuleType("llama_index.core")
    li_llms = types.ModuleType("llama_index.core.llms")

    class _FakeCompletionResponse:
        text = "llamaindex response"

    class LLM:
        model = "gpt-4o"

        def complete(self, prompt, *args, **kwargs):
            return _FakeCompletionResponse()

        async def acomplete(self, prompt, *args, **kwargs):
            return _FakeCompletionResponse()

    li_llms.LLM = LLM

    for name, mod in [
        ("llama_index", li_core),
        ("llama_index.core", li_core_sub),
        ("llama_index.core.llms", li_llms),
    ]:
        sys.modules.setdefault(name, mod)

    return LLM


def _cleanup_llama_index_stub():
    for name in ["llama_index", "llama_index.core", "llama_index.core.llms"]:
        sys.modules.pop(name, None)


class TestLlamaIndexPatch:
    def setup_method(self):
        self.LLM = _make_llama_index_stub()

    def teardown_method(self):
        _uninstrument()
        _cleanup_llama_index_stub()

    def test_patch_llama_index_is_idempotent(self):
        from ghostrace.auto_instrument import _patch_llama_index
        _patch_llama_index()
        _patch_llama_index()
        assert "llama_index" in _PATCHED

    def test_complete_records_event(self):
        from ghostrace.auto_instrument import _patch_llama_index
        _patch_llama_index()

        llm = self.LLM()
        llm.complete("Tell me a joke")

        events = _collected_events()
        assert len(events) == 1
        ev = events[0]
        assert ev.event_type == "llm_call"
        assert ev.prompt == "Tell me a joke"
        assert ev.response == "llamaindex response"
        assert ev.model == "gpt-4o"

    def test_complete_error_records_error_event(self, _setup):
        from ghostrace.auto_instrument import _patch_llama_index

        # Make the stub raise BEFORE patching so the closure captures it
        def _raising_complete(self_inner, prompt, *args, **kwargs):
            raise RuntimeError("llama_index fail")

        self.LLM.complete = _raising_complete
        _patch_llama_index()

        llm = self.LLM()
        with pytest.raises(RuntimeError):
            llm.complete("oops")

        written = _collected_events()
        assert any(
            e.event_type == "error" and e.error_type == "RuntimeError"
            for e in written
        )

    @pytest.mark.asyncio
    async def test_acomplete_records_event(self):
        from ghostrace.auto_instrument import _patch_llama_index
        _patch_llama_index()

        llm = self.LLM()
        await llm.acomplete("async joke")

        events = _collected_events()
        assert any(e.event_type == "llm_call" and e.prompt == "async joke" for e in events)


# ── Google Generative AI stubs + tests ───────────────────────────────────────


def _make_google_genai_stub():
    google_pkg = types.ModuleType("google")
    google_genai = types.ModuleType("google.generativeai")

    class _FakeUsage:
        prompt_token_count = 12
        candidates_token_count = 6

    class _FakeResponse:
        text = "gemini says hello"
        usage_metadata = _FakeUsage()

    class GenerativeModel:
        model_name = "gemini-2.0-flash"

        def generate_content(self, contents, *args, **kwargs):
            return _FakeResponse()

        async def generate_content_async(self, contents, *args, **kwargs):
            return _FakeResponse()

    google_genai.GenerativeModel = GenerativeModel

    for name, mod in [
        ("google", google_pkg),
        ("google.generativeai", google_genai),
    ]:
        sys.modules.setdefault(name, mod)

    return GenerativeModel


def _cleanup_google_stub():
    sys.modules.pop("google.generativeai", None)
    # only remove google if we added it
    if hasattr(sys.modules.get("google"), "generativeai"):
        sys.modules.pop("google", None)


class TestGoogleGenAIPatch:
    def setup_method(self):
        self.GenModel = _make_google_genai_stub()

    def teardown_method(self):
        _uninstrument()
        _cleanup_google_stub()

    def test_patch_google_genai_is_idempotent(self):
        from ghostrace.auto_instrument import _patch_google_genai
        _patch_google_genai()
        _patch_google_genai()
        assert "google_genai" in _PATCHED

    def test_generate_content_records_event(self):
        from ghostrace.auto_instrument import _patch_google_genai
        _patch_google_genai()

        model = self.GenModel()
        model.generate_content("What is AI?")

        events = _collected_events()
        assert len(events) == 1
        ev = events[0]
        assert ev.event_type == "llm_call"
        assert ev.prompt == "What is AI?"
        assert ev.response == "gemini says hello"
        assert ev.model == "gemini-2.0-flash"
        assert ev.tokens_in == 12
        assert ev.tokens_out == 6

    def test_generate_content_error_records_error_event(self, _setup):
        from ghostrace.auto_instrument import _patch_google_genai

        # Make the stub raise BEFORE patching so the closure captures it
        def _raising_gen(self_inner, contents, *args, **kwargs):
            raise ConnectionError("quota exceeded")

        self.GenModel.generate_content = _raising_gen
        _patch_google_genai()

        model = self.GenModel()
        with pytest.raises(ConnectionError):
            model.generate_content("oops")

        written = _collected_events()
        assert any(
            e.event_type == "error" and e.error_type == "ConnectionError"
            for e in written
        )

    @pytest.mark.asyncio
    async def test_generate_content_async_records_event(self):
        from ghostrace.auto_instrument import _patch_google_genai
        _patch_google_genai()

        model = self.GenModel()
        await model.generate_content_async("async gemini")

        events = _collected_events()
        assert any(e.event_type == "llm_call" and e.prompt == "async gemini" for e in events)


# ── auto_instrument() selective flags ─────────────────────────────────────────


class TestAutoInstrumentFlags:
    def teardown_method(self):
        _uninstrument()
        _cleanup_langchain_stub()
        _cleanup_llama_index_stub()
        _cleanup_google_stub()

    def test_selective_disable_langchain(self):
        _make_langchain_stub()
        _make_llama_index_stub()
        ghostrace.auto_instrument(langchain=False, llama_index=True, google_genai=False)
        assert "langchain" not in _PATCHED
        assert "llama_index" in _PATCHED

    def test_selective_disable_llama_index(self):
        _make_langchain_stub()
        _make_llama_index_stub()
        ghostrace.auto_instrument(langchain=True, llama_index=False, google_genai=False)
        assert "langchain" in _PATCHED
        assert "llama_index" not in _PATCHED

    def test_uninstrument_clears_all(self):
        _make_langchain_stub()
        _make_llama_index_stub()
        _make_google_genai_stub()
        ghostrace.auto_instrument(openai=False, anthropic=False)
        assert len(_PATCHED) > 0
        _uninstrument()
        assert len(_PATCHED) == 0
