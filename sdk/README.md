# ghostrace

**AI agent observability.** Full session replay, cost tracking, loop detection, and error visibility — in 3 lines of Python.

[![PyPI version](https://img.shields.io/pypi/v/ghostrace)](https://pypi.org/project/ghostrace/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Install

```bash
pip install ghostrace
```

---

## Quick start

```python
import ghostrace

# 1. Initialize once (e.g. in your agent's entry point)
ghostrace.init(api_key="gr_xxxx", project="my-agent")

# 2. Decorate any LLM call
@ghostrace.trace
def call_llm(prompt: str) -> str:
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

# 3. Decorate tools
@ghostrace.trace(kind="tool")
def search_web(query: str) -> list:
    ...  # your tool logic

# Async works identically — no changes needed
@ghostrace.trace
async def async_llm_call(prompt: str) -> str:
    ...
```

That's it. Every call is now traced with prompt, response, tokens, cost, latency, and errors — visible in the [Ghostrace dashboard](https://ghostrace.dev).

---

## Group calls into sessions

```python
with ghostrace.session(name="user-request-abc") as s:
    s.tag("user_id", "u_123")
    s.tag("environment", "production")
    result = my_agent.run(user_input)

# Async
async with ghostrace.session(name="async-run") as s:
    s.tag("task", "summarise")
    result = await my_async_agent.run(prompt)
```

All events inside the `with` block are grouped under one session in the dashboard.

---

## Zero-touch instrumentation

```python
ghostrace.init(api_key="gr_xxxx", project="my-agent")
ghostrace.auto_instrument()  # patches openai + anthropic automatically

# Now every openai.chat.completions.create() call is traced — no decorator needed
response = client.chat.completions.create(model="gpt-4o", messages=[...])
```

---

## What gets captured automatically

| Field | Description |
|---|---|
| `event_type` | `llm_call` \| `tool_call` \| `error` \| `custom` |
| `model` | Extracted from response object (e.g. `gpt-4o`) |
| `prompt` | Full input text or serialised args |
| `response` | Full output text |
| `tokens_in` | Input token count |
| `tokens_out` | Output token count |
| `cost_usd` | Calculated from built-in pricing table |
| `latency_ms` | Wall clock time in milliseconds |
| `timestamp` | UTC ISO8601 |
| `error_type` | Exception class name (if the call raised) |
| `error_message` | Exception message |
| `stack_trace` | Full Python traceback |
| `tool_name` | Function name (for `kind="tool"` traces) |
| `session_id` | UUID, auto-generated or user-provided |
| `sequence_number` | Ordering within session |

---

## Offline / local mode

```python
# No backend needed — write traces to ~/.ghostrace/traces/ only
ghostrace.init(local_only=True, project="dev")
```

Traces are written to `~/.ghostrace/traces/<YYYY-MM-DD>.ndjson` as newline-delimited JSON. You can `cat` or `jq` them locally.

---

## Reliability guarantees

- **SDK never crashes your agent.** All internal errors are caught at the decorator level and logged to stderr — never propagated.
- **Backend unreachable?** Events are buffered to `~/.ghostrace/buffer/` and replayed on the next startup.
- **Retry logic:** 3 attempts with exponential backoff (1s → 2s → 4s) before buffering.
- **Serialisation fails?** That field is skipped with a warning — the rest of the event is still captured.

---

## Supported models (cost tracking)

Built-in pricing for: OpenAI (GPT-4o, GPT-4o mini, o1, o3, o4-mini), Anthropic (Claude Opus 4, Sonnet 4, Haiku 4), Google (Gemini 1.5 Pro/Flash, 2.0 Flash, 2.5 Pro/Flash), Mistral, Cohere, and a fallback for unknown models.

---

## Development

```bash
cd sdk
pip install -e ".[dev]"
pytest tests/ -v --asyncio-mode=auto
```

---

## Links

- [Dashboard](https://ghostrace.dev)
- [Documentation](https://docs.ghostrace.dev)
- [GitHub](https://github.com/ghostrace/ghostrace-python)
- [PyPI](https://pypi.org/project/ghostrace/)
