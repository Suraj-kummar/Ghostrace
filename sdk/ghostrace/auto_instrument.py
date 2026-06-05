"""
ghostrace.auto_instrument
~~~~~~~~~~~~~~~~~~~~~~~~~
Zero-touch monkey-patching of popular LLM libraries.

Call once after ghostrace.init():
    ghostrace.auto_instrument()

Supports:
  - openai >= 1.0         (ChatCompletion sync + async)
  - anthropic >= 0.20     (Messages sync + async)
  - langchain >= 0.1      (ChatOpenAI, ChatAnthropic, BaseLLM._generate)
  - llama_index >= 0.10   (LLM.complete / acomplete)
  - google-generativeai   (GenerativeModel.generate_content sync + async)

Design rules:
  - Idempotent: calling multiple times does NOT double-patch.
  - Reversible: _uninstrument() restores originals (used in tests).
  - All patch errors are caught; a library failing to patch must not crash.
  - Only patches at the call site — doesn't touch class __init__.
"""
from __future__ import annotations

import asyncio
import functools
import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Set

from .models import TraceEvent
from .pricing import calculate_cost

logger = logging.getLogger(__name__)

_PATCHED: Set[str] = set()  # tracks which libs are already patched
_ORIGINALS: dict = {}       # stores original methods for _uninstrument()

# ── Helpers ───────────────────────────────────────────────────────────────────


def _record(event: TraceEvent) -> None:
    """Push to collector, catching all errors."""
    try:
        from .collector import get_collector

        get_collector().record(event)
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace auto_instrument record error: %s", exc)


def _openai_event(
    response: Any,
    start: float,
    exc: Optional[BaseException],
    prompt_messages: Any,
) -> TraceEvent:
    latency_ms = int((time.perf_counter() - start) * 1000)

    if exc is not None:
        import traceback

        return TraceEvent(
            event_type="error",
            timestamp=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )

    model: Optional[str] = getattr(response, "model", None)
    usage = getattr(response, "usage", None)
    tokens_in: Optional[int] = getattr(usage, "prompt_tokens", None) if usage else None
    tokens_out: Optional[int] = getattr(usage, "completion_tokens", None) if usage else None
    cost: Optional[float] = None
    if model and tokens_in is not None:
        cost = calculate_cost(model, tokens_in, tokens_out or 0)

    # Extract text from first choice
    response_text: Optional[str] = None
    choices = getattr(response, "choices", None)
    if choices:
        msg = getattr(choices[0], "message", None)
        if msg:
            response_text = getattr(msg, "content", None)

    # Serialise prompt messages
    prompt_str: Optional[str] = None
    try:
        import json

        prompt_str = json.dumps(prompt_messages, default=str)
    except Exception:  # noqa: BLE001
        prompt_str = repr(prompt_messages)

    return TraceEvent(
        event_type="llm_call",
        timestamp=datetime.now(timezone.utc),
        latency_ms=latency_ms,
        model=model,
        prompt=prompt_str,
        response=response_text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
    )


def _anthropic_event(
    response: Any,
    start: float,
    exc: Optional[BaseException],
    prompt_messages: Any,
    system: Any = None,
    model_name: Optional[str] = None,
) -> TraceEvent:
    latency_ms = int((time.perf_counter() - start) * 1000)

    if exc is not None:
        import traceback

        return TraceEvent(
            event_type="error",
            timestamp=datetime.now(timezone.utc),
            latency_ms=latency_ms,
            error_type=type(exc).__name__,
            error_message=str(exc),
            stack_trace=traceback.format_exc(),
        )

    model = getattr(response, "model", None) or model_name
    usage = getattr(response, "usage", None)
    tokens_in: Optional[int] = getattr(usage, "input_tokens", None) if usage else None
    tokens_out: Optional[int] = getattr(usage, "output_tokens", None) if usage else None
    cost: Optional[float] = None
    if model and tokens_in is not None:
        cost = calculate_cost(model, tokens_in, tokens_out or 0)

    response_text: Optional[str] = None
    content = getattr(response, "content", None)
    if isinstance(content, list):
        parts = [getattr(b, "text", "") for b in content if hasattr(b, "text")]
        response_text = "\n".join(parts) or None

    try:
        import json

        prompt_str = json.dumps(prompt_messages, default=str)
        if system:
            prompt_str = f"[system]: {system}\n" + prompt_str
    except Exception:  # noqa: BLE001
        prompt_str = repr(prompt_messages)

    return TraceEvent(
        event_type="llm_call",
        timestamp=datetime.now(timezone.utc),
        latency_ms=latency_ms,
        model=model,
        prompt=prompt_str,
        response=response_text,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost,
    )


# ── OpenAI patching ───────────────────────────────────────────────────────────


def _patch_openai() -> None:
    """Patch openai.chat.completions.create (sync + async)."""
    if "openai" in _PATCHED:
        return
    try:
        import openai

        client_cls = openai.OpenAI  # type: ignore[attr-defined]
        async_client_cls = openai.AsyncOpenAI  # type: ignore[attr-defined]

        # ── Sync ─────────────────────────────────────────────────────────────
        _orig_create = openai.resources.chat.completions.Completions.create

        @functools.wraps(_orig_create)
        def _patched_create(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", args[0] if args else None)
            try:
                response = _orig_create(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _openai_event(response, start, exc_caught, messages)
                _record(event)

        _ORIGINALS["openai_create"] = _orig_create
        openai.resources.chat.completions.Completions.create = _patched_create  # type: ignore[method-assign]

        # ── Async ─────────────────────────────────────────────────────────────
        _orig_acreate = openai.resources.chat.completions.AsyncCompletions.create

        @functools.wraps(_orig_acreate)
        async def _patched_acreate(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", args[0] if args else None)
            try:
                response = await _orig_acreate(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _openai_event(response, start, exc_caught, messages)
                _record(event)

        _ORIGINALS["openai_acreate"] = _orig_acreate
        openai.resources.chat.completions.AsyncCompletions.create = _patched_acreate  # type: ignore[method-assign]

        _PATCHED.add("openai")
        logger.debug("ghostrace: patched openai.chat.completions.create")

    except ImportError:
        pass  # openai not installed — skip silently
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not patch openai: %s", exc)


# ── Anthropic patching ────────────────────────────────────────────────────────


def _patch_anthropic() -> None:
    """Patch anthropic.resources.messages.Messages.create (sync + async)."""
    if "anthropic" in _PATCHED:
        return
    try:
        import anthropic.resources.messages as _msgs

        _orig_create = _msgs.Messages.create

        @functools.wraps(_orig_create)
        def _patched_create(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", [])
            system = kwargs.get("system")
            model_name = kwargs.get("model")
            try:
                response = _orig_create(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _anthropic_event(response, start, exc_caught, messages, system, model_name)
                _record(event)

        _ORIGINALS["anthropic_create"] = _orig_create
        _msgs.Messages.create = _patched_create  # type: ignore[method-assign]

        # Async
        _orig_acreate = _msgs.AsyncMessages.create

        @functools.wraps(_orig_acreate)
        async def _patched_acreate(self: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            messages = kwargs.get("messages", [])
            system = kwargs.get("system")
            model_name = kwargs.get("model")
            try:
                response = await _orig_acreate(self, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                event = _anthropic_event(response, start, exc_caught, messages, system, model_name)
                _record(event)

        _ORIGINALS["anthropic_acreate"] = _orig_acreate
        _msgs.AsyncMessages.create = _patched_acreate  # type: ignore[method-assign]

        _PATCHED.add("anthropic")
        logger.debug("ghostrace: patched anthropic.resources.messages.Messages.create")

    except ImportError:
        pass  # anthropic not installed
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not patch anthropic: %s", exc)


# ── LangChain patching ────────────────────────────────────────────────────────


def _patch_langchain() -> None:
    """Patch LangChain BaseChatModel._generate and BaseLLM._generate (sync + async)."""
    if "langchain" in _PATCHED:
        return
    try:
        from langchain_core.language_models.chat_models import BaseChatModel
        from langchain_core.language_models.llms import BaseLLM
        from langchain_core.messages import BaseMessage

        def _lc_event(
            response: Any,
            start: float,
            exc: Optional[BaseException],
            prompt_str: Optional[str],
            model_name: Optional[str] = None,
        ) -> TraceEvent:
            latency_ms = int((time.perf_counter() - start) * 1000)
            if exc is not None:
                import traceback as _tb
                return TraceEvent(
                    event_type="error",
                    timestamp=datetime.now(timezone.utc),
                    latency_ms=latency_ms,
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    stack_trace=_tb.format_exc(),
                )
            # Extract text from LangChain ChatResult / LLMResult
            response_text: Optional[str] = None
            tokens_in: Optional[int] = None
            tokens_out: Optional[int] = None
            cost: Optional[float] = None
            model: Optional[str] = model_name
            if response is not None:
                try:
                    # ChatResult: response.generations[0][0].text
                    gens = getattr(response, "generations", None)
                    if gens and gens[0]:
                        first = gens[0][0]
                        response_text = getattr(first, "text", None)
                    # LLMOutput metadata
                    llm_out = getattr(response, "llm_output", None) or {}
                    token_usage = llm_out.get("token_usage", {})
                    tokens_in = token_usage.get("prompt_tokens")
                    tokens_out = token_usage.get("completion_tokens")
                    model = llm_out.get("model_name") or model_name
                    if model and tokens_in is not None:
                        cost = calculate_cost(model, tokens_in, tokens_out or 0)
                except Exception:
                    pass
            return TraceEvent(
                event_type="llm_call",
                timestamp=datetime.now(timezone.utc),
                latency_ms=latency_ms,
                model=model,
                prompt=prompt_str,
                response=response_text,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                cost_usd=cost,
            )

        # ── BaseChatModel._generate ──────────────────────────────────────────
        _orig_chat_gen = BaseChatModel._generate
        _ORIGINALS["langchain_chat_generate"] = _orig_chat_gen

        @functools.wraps(_orig_chat_gen)
        def _patched_chat_gen(self: Any, messages: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            try:
                prompt_str = " | ".join(
                    getattr(m, "content", str(m)) for m in messages
                ) if hasattr(messages, "__iter__") else str(messages)
            except Exception:
                prompt_str = repr(messages)
            try:
                response = _orig_chat_gen(self, messages, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                model_name = getattr(self, "model_name", None) or getattr(self, "model", None)
                event = _lc_event(response, start, exc_caught, prompt_str, model_name)
                _record(event)

        BaseChatModel._generate = _patched_chat_gen  # type: ignore[method-assign]

        # ── BaseChatModel._agenerate ─────────────────────────────────────────
        _orig_chat_agen = BaseChatModel._agenerate
        _ORIGINALS["langchain_chat_agenerate"] = _orig_chat_agen

        @functools.wraps(_orig_chat_agen)
        async def _patched_chat_agen(self: Any, messages: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            try:
                prompt_str = " | ".join(
                    getattr(m, "content", str(m)) for m in messages
                ) if hasattr(messages, "__iter__") else str(messages)
            except Exception:
                prompt_str = repr(messages)
            try:
                response = await _orig_chat_agen(self, messages, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                model_name = getattr(self, "model_name", None) or getattr(self, "model", None)
                event = _lc_event(response, start, exc_caught, prompt_str, model_name)
                _record(event)

        BaseChatModel._agenerate = _patched_chat_agen  # type: ignore[method-assign]

        # ── BaseLLM._generate ────────────────────────────────────────────────
        _orig_llm_gen = BaseLLM._generate
        _ORIGINALS["langchain_llm_generate"] = _orig_llm_gen

        @functools.wraps(_orig_llm_gen)
        def _patched_llm_gen(self: Any, prompts: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            prompt_str = prompts[0] if isinstance(prompts, list) and prompts else repr(prompts)
            try:
                response = _orig_llm_gen(self, prompts, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                model_name = getattr(self, "model_name", None) or getattr(self, "model", None)
                event = _lc_event(response, start, exc_caught, prompt_str, model_name)
                _record(event)

        BaseLLM._generate = _patched_llm_gen  # type: ignore[method-assign]

        _PATCHED.add("langchain")
        logger.debug("ghostrace: patched langchain BaseChatModel + BaseLLM")

    except ImportError:
        pass  # langchain not installed
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not patch langchain: %s", exc)


# ── LlamaIndex patching ───────────────────────────────────────────────────────


def _patch_llama_index() -> None:
    """Patch llama_index.core.llms.LLM.complete and acomplete."""
    if "llama_index" in _PATCHED:
        return
    try:
        from llama_index.core.llms import LLM

        _orig_complete = LLM.complete
        _ORIGINALS["llama_index_complete"] = _orig_complete

        @functools.wraps(_orig_complete)
        def _patched_complete(self: Any, prompt: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            prompt_str = str(prompt)
            try:
                response = _orig_complete(self, prompt, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                latency_ms = int((time.perf_counter() - start) * 1000)
                if exc_caught is not None:
                    import traceback as _tb
                    event = TraceEvent(
                        event_type="error",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        error_type=type(exc_caught).__name__,
                        error_message=str(exc_caught),
                        stack_trace=_tb.format_exc(),
                    )
                else:
                    resp_text = getattr(response, "text", None) or str(response)
                    model_name = getattr(self, "model", None)
                    event = TraceEvent(
                        event_type="llm_call",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        model=str(model_name) if model_name else None,
                        prompt=prompt_str,
                        response=resp_text,
                    )
                _record(event)

        LLM.complete = _patched_complete  # type: ignore[method-assign]

        _orig_acomplete = LLM.acomplete
        _ORIGINALS["llama_index_acomplete"] = _orig_acomplete

        @functools.wraps(_orig_acomplete)
        async def _patched_acomplete(self: Any, prompt: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            prompt_str = str(prompt)
            try:
                response = await _orig_acomplete(self, prompt, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                latency_ms = int((time.perf_counter() - start) * 1000)
                if exc_caught is not None:
                    import traceback as _tb
                    event = TraceEvent(
                        event_type="error",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        error_type=type(exc_caught).__name__,
                        error_message=str(exc_caught),
                        stack_trace=_tb.format_exc(),
                    )
                else:
                    resp_text = getattr(response, "text", None) or str(response)
                    model_name = getattr(self, "model", None)
                    event = TraceEvent(
                        event_type="llm_call",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        model=str(model_name) if model_name else None,
                        prompt=prompt_str,
                        response=resp_text,
                    )
                _record(event)

        LLM.acomplete = _patched_acomplete  # type: ignore[method-assign]

        _PATCHED.add("llama_index")
        logger.debug("ghostrace: patched llama_index.core.llms.LLM")

    except ImportError:
        pass  # llama_index not installed
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not patch llama_index: %s", exc)


# ── Google Generative AI patching ─────────────────────────────────────────────


def _patch_google_genai() -> None:
    """Patch google.generativeai.GenerativeModel.generate_content (sync + async)."""
    if "google_genai" in _PATCHED:
        return
    try:
        import google.generativeai as genai

        GenModel = genai.GenerativeModel
        _orig_gen = GenModel.generate_content
        _ORIGINALS["google_genai_generate"] = _orig_gen

        @functools.wraps(_orig_gen)
        def _patched_gen(self: Any, contents: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            try:
                prompt_str = str(contents)
            except Exception:
                prompt_str = None
            try:
                response = _orig_gen(self, contents, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                latency_ms = int((time.perf_counter() - start) * 1000)
                if exc_caught is not None:
                    import traceback as _tb
                    event = TraceEvent(
                        event_type="error",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        error_type=type(exc_caught).__name__,
                        error_message=str(exc_caught),
                        stack_trace=_tb.format_exc(),
                    )
                else:
                    resp_text: Optional[str] = None
                    tokens_in: Optional[int] = None
                    tokens_out: Optional[int] = None
                    model_name: Optional[str] = getattr(self, "model_name", None)
                    try:
                        resp_text = response.text
                        usage = getattr(response, "usage_metadata", None)
                        if usage:
                            tokens_in = getattr(usage, "prompt_token_count", None)
                            tokens_out = getattr(usage, "candidates_token_count", None)
                        cost = calculate_cost(model_name or "", tokens_in or 0, tokens_out or 0)
                    except Exception:
                        cost = None
                    event = TraceEvent(
                        event_type="llm_call",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        model=model_name,
                        prompt=prompt_str,
                        response=resp_text,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                        cost_usd=cost if tokens_in else None,
                    )
                _record(event)

        GenModel.generate_content = _patched_gen  # type: ignore[method-assign]

        # ── Async ─────────────────────────────────────────────────────────────
        _orig_agen = GenModel.generate_content_async
        _ORIGINALS["google_genai_agenerate"] = _orig_agen

        @functools.wraps(_orig_agen)
        async def _patched_agen(self: Any, contents: Any, *args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            exc_caught: Optional[BaseException] = None
            response: Any = None
            try:
                prompt_str = str(contents)
            except Exception:
                prompt_str = None
            try:
                response = await _orig_agen(self, contents, *args, **kwargs)
                return response
            except Exception as e:
                exc_caught = e
                raise
            finally:
                latency_ms = int((time.perf_counter() - start) * 1000)
                if exc_caught is not None:
                    import traceback as _tb
                    event = TraceEvent(
                        event_type="error",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        error_type=type(exc_caught).__name__,
                        error_message=str(exc_caught),
                        stack_trace=_tb.format_exc(),
                    )
                else:
                    resp_text = None
                    tokens_in = None
                    tokens_out = None
                    model_name = getattr(self, "model_name", None)
                    try:
                        resp_text = response.text
                        usage = getattr(response, "usage_metadata", None)
                        if usage:
                            tokens_in = getattr(usage, "prompt_token_count", None)
                            tokens_out = getattr(usage, "candidates_token_count", None)
                    except Exception:
                        pass
                    event = TraceEvent(
                        event_type="llm_call",
                        timestamp=datetime.now(timezone.utc),
                        latency_ms=latency_ms,
                        model=model_name,
                        prompt=prompt_str,
                        response=resp_text,
                        tokens_in=tokens_in,
                        tokens_out=tokens_out,
                    )
                _record(event)

        GenModel.generate_content_async = _patched_agen  # type: ignore[method-assign]

        _PATCHED.add("google_genai")
        logger.debug("ghostrace: patched google.generativeai.GenerativeModel")

    except ImportError:
        pass  # google-generativeai not installed
    except Exception as exc:  # noqa: BLE001
        logger.warning("ghostrace: could not patch google_genai: %s", exc)


# ── Public API ────────────────────────────────────────────────────────────────


def auto_instrument(
    openai: bool = True,
    anthropic: bool = True,
    langchain: bool = True,
    llama_index: bool = True,
    google_genai: bool = True,
) -> None:
    """
    Automatically trace all calls to supported LLM libraries.

    Call this once after ghostrace.init().  Safe to call multiple times.
    Libraries that are not installed are silently skipped.

    Args:
        openai:      Patch openai.chat.completions.create  (default: True)
        anthropic:   Patch anthropic.messages.create       (default: True)
        langchain:   Patch langchain BaseChatModel/_generate (default: True)
        llama_index: Patch llama_index.core.llms.LLM.complete (default: True)
        google_genai: Patch google.generativeai.GenerativeModel (default: True)

    Currently instruments:
      - openai        (sync + async ChatCompletion)
      - anthropic     (sync + async Messages)
      - langchain     (BaseChatModel + BaseLLM, sync + async)
      - llama_index   (LLM.complete + acomplete)
      - google_genai  (GenerativeModel.generate_content sync + async)
    """
    if openai:
        _patch_openai()
    if anthropic:
        _patch_anthropic()
    if langchain:
        _patch_langchain()
    if llama_index:
        _patch_llama_index()
    if google_genai:
        _patch_google_genai()


def _uninstrument() -> None:
    """
    Restore all patched methods to their originals.
    Used in tests — not part of the public API.
    """
    try:
        if "openai" in _PATCHED:
            import openai
            if "openai_create" in _ORIGINALS:
                openai.resources.chat.completions.Completions.create = _ORIGINALS.pop("openai_create")
            if "openai_acreate" in _ORIGINALS:
                openai.resources.chat.completions.AsyncCompletions.create = _ORIGINALS.pop("openai_acreate")
    except Exception:
        pass
    try:
        if "anthropic" in _PATCHED:
            import anthropic.resources.messages as _msgs
            if "anthropic_create" in _ORIGINALS:
                _msgs.Messages.create = _ORIGINALS.pop("anthropic_create")
            if "anthropic_acreate" in _ORIGINALS:
                _msgs.AsyncMessages.create = _ORIGINALS.pop("anthropic_acreate")
    except Exception:
        pass
    try:
        if "langchain" in _PATCHED:
            from langchain_core.language_models.chat_models import BaseChatModel
            from langchain_core.language_models.llms import BaseLLM
            if "langchain_chat_generate" in _ORIGINALS:
                BaseChatModel._generate = _ORIGINALS.pop("langchain_chat_generate")
            if "langchain_chat_agenerate" in _ORIGINALS:
                BaseChatModel._agenerate = _ORIGINALS.pop("langchain_chat_agenerate")
            if "langchain_llm_generate" in _ORIGINALS:
                BaseLLM._generate = _ORIGINALS.pop("langchain_llm_generate")
    except Exception:
        pass
    try:
        if "llama_index" in _PATCHED:
            from llama_index.core.llms import LLM
            if "llama_index_complete" in _ORIGINALS:
                LLM.complete = _ORIGINALS.pop("llama_index_complete")
            if "llama_index_acomplete" in _ORIGINALS:
                LLM.acomplete = _ORIGINALS.pop("llama_index_acomplete")
    except Exception:
        pass
    try:
        if "google_genai" in _PATCHED:
            import google.generativeai as genai
            if "google_genai_generate" in _ORIGINALS:
                genai.GenerativeModel.generate_content = _ORIGINALS.pop("google_genai_generate")
            if "google_genai_agenerate" in _ORIGINALS:
                genai.GenerativeModel.generate_content_async = _ORIGINALS.pop("google_genai_agenerate")
    except Exception:
        pass
    _PATCHED.clear()
    _ORIGINALS.clear()
    logger.debug("ghostrace: uninstrumented (all originals restored)")
