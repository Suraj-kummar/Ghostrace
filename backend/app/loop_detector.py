"""
ghostrace.backend.loop_detector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Pure-Python loop detection for Ghostrace trace sessions.

Detects three categories of potential infinite-loop behaviour:

1. **Repeated LLM prompts**  — identical (hashed) prompts sent to an LLM
   three or more times within the same session.

2. **Repeated tool calls**   — the same tool called with identical JSON
   arguments three or more times.

3. **Consecutive same-model calls** — the same LLM model invoked in an
   unbroken run of three or more calls with no tool/error event in between.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Minimum identical occurrences required to flag a loop
LOOP_REPEAT_THRESHOLD = 3


# ── Data structures ───────────────────────────────────────────────────────────

@dataclass
class LoopOccurrence:
    kind: str           # "llm_prompt" | "tool_call" | "consecutive_model"
    description: str
    event_ids: List[str] = field(default_factory=list)
    repeat_count: int = 0
    severity: str = "warning"   # "warning" | "critical"


@dataclass
class LoopDetectionResult:
    loop_detected: bool
    occurrences: List[LoopOccurrence] = field(default_factory=list)

    @property
    def summary(self) -> str:
        if not self.loop_detected:
            return ""
        return "; ".join(
            f"{o.description} (×{o.repeat_count})" for o in self.occurrences
        )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get(event: Any, attr: str) -> Any:
    """Unified attribute access for SQLAlchemy ORM objects and plain dicts."""
    if isinstance(event, dict):
        return event.get(attr)
    return getattr(event, attr, None)


def _hash_text(text: str) -> str:
    """Short stable hash for a prompt string."""
    return hashlib.md5(
        text.strip().lower().encode(), usedforsecurity=False
    ).hexdigest()[:16]


def _hash_tool(name: Optional[str], inp: Optional[Any]) -> str:
    """Stable hash for (tool_name, tool_input) pair."""
    payload = f"{name}:{json.dumps(inp, sort_keys=True, default=str)}"
    return hashlib.md5(payload.encode(), usedforsecurity=False).hexdigest()[:16]


# ── Main entry point ──────────────────────────────────────────────────────────

def detect_loops(events: List[Any]) -> LoopDetectionResult:
    """
    Analyse a list of trace events and return a LoopDetectionResult.

    Compatible with both SQLAlchemy ORM ``TraceEvent`` objects and plain dicts.

    Args:
        events: Ordered list of trace event objects/dicts for a single session.

    Returns:
        LoopDetectionResult with ``loop_detected`` bool and ``occurrences`` list.
    """
    if len(events) < LOOP_REPEAT_THRESHOLD:
        return LoopDetectionResult(loop_detected=False)

    occurrences: List[LoopOccurrence] = []

    # ── 1. Repeated LLM prompts ───────────────────────────────────────────────
    prompt_map: Dict[str, List[str]] = {}   # hash → [event_id, ...]

    for e in events:
        if _get(e, "event_type") == "llm_call":
            prompt = _get(e, "prompt")
            if prompt:
                prompt_map.setdefault(_hash_text(prompt), []).append(_get(e, "id"))

    for eids in prompt_map.values():
        if len(eids) >= LOOP_REPEAT_THRESHOLD:
            occurrences.append(LoopOccurrence(
                kind="llm_prompt",
                description=f"Identical LLM prompt sent {len(eids)} times",
                event_ids=eids,
                repeat_count=len(eids),
                severity="critical" if len(eids) >= 5 else "warning",
            ))

    # ── 2. Repeated tool calls with identical arguments ───────────────────────
    tool_map: Dict[str, List[tuple]] = {}   # hash → [(event_id, tool_name), ...]

    for e in events:
        if _get(e, "event_type") == "tool_call":
            name = _get(e, "tool_name")
            inp = _get(e, "tool_input")
            if name:
                h = _hash_tool(name, inp)
                tool_map.setdefault(h, []).append((_get(e, "id"), name))

    for items in tool_map.values():
        if len(items) >= LOOP_REPEAT_THRESHOLD:
            eids = [i[0] for i in items]
            tname = items[0][1]
            occurrences.append(LoopOccurrence(
                kind="tool_call",
                description=f"Tool '{tname}' called with identical args {len(items)} times",
                event_ids=eids,
                repeat_count=len(items),
                severity="critical" if len(items) >= 5 else "warning",
            ))

    # ── 3. Consecutive same-model calls ───────────────────────────────────────
    sorted_events = sorted(events, key=lambda e: _get(e, "sequence_number") or 0)

    run_model: Optional[str] = None
    run_ids: List[str] = []

    def _flush_run() -> None:
        if len(run_ids) >= LOOP_REPEAT_THRESHOLD:
            occurrences.append(LoopOccurrence(
                kind="consecutive_model",
                description=f"Model '{run_model}' called {len(run_ids)} times consecutively",
                event_ids=list(run_ids),
                repeat_count=len(run_ids),
                severity="warning",
            ))

    for e in sorted_events:
        etype = _get(e, "event_type")
        model = _get(e, "model")
        eid = _get(e, "id")

        if etype == "llm_call" and model:
            if model == run_model:
                run_ids.append(eid)
            else:
                _flush_run()
                run_model = model
                run_ids = [eid]
        else:
            _flush_run()
            run_model = None
            run_ids = []

    _flush_run()  # flush any trailing run

    # ── De-duplicate: same event_id sets, keep highest severity first ──────────
    seen: set = set()
    deduped: List[LoopOccurrence] = []
    for occ in sorted(occurrences, key=lambda o: 0 if o.severity == "critical" else 1):
        key = frozenset(occ.event_ids)
        if key not in seen:
            seen.add(key)
            deduped.append(occ)

    return LoopDetectionResult(loop_detected=bool(deduped), occurrences=deduped)
