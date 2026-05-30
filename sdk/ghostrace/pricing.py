"""
ghostrace.pricing
~~~~~~~~~~~~~~~~~
Built-in model pricing table and cost calculation helpers.

Prices are per-token (USD).  All values sourced from official provider
pricing pages as of May 2026 — update this table as prices change.
"""
from __future__ import annotations

from typing import Dict, Tuple

# ── Pricing table ────────────────────────────────────────────────────────────
# Format: model_name → {"in": price_per_token, "out": price_per_token}
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    # ── OpenAI ──────────────────────────────────────────────────────────────
    "gpt-4o":                {"in": 0.0000025,   "out": 0.000010},
    "gpt-4o-2024-08-06":     {"in": 0.0000025,   "out": 0.000010},
    "gpt-4o-2024-05-13":     {"in": 0.000005,    "out": 0.000015},
    "gpt-4o-mini":           {"in": 0.00000015,  "out": 0.0000006},
    "gpt-4o-mini-2024-07-18":{"in": 0.00000015,  "out": 0.0000006},
    "gpt-4-turbo":           {"in": 0.000010,    "out": 0.000030},
    "gpt-4-turbo-2024-04-09":{"in": 0.000010,    "out": 0.000030},
    "gpt-4":                 {"in": 0.000030,    "out": 0.000060},
    "gpt-3.5-turbo":         {"in": 0.0000005,   "out": 0.0000015},
    "gpt-3.5-turbo-0125":    {"in": 0.0000005,   "out": 0.0000015},
    "o1":                    {"in": 0.000015,    "out": 0.000060},
    "o1-mini":               {"in": 0.000003,    "out": 0.000012},
    "o3":                    {"in": 0.000010,    "out": 0.000040},
    "o3-mini":               {"in": 0.0000011,   "out": 0.0000044},
    "o4-mini":               {"in": 0.0000011,   "out": 0.0000044},

    # ── Anthropic ───────────────────────────────────────────────────────────
    "claude-opus-4":         {"in": 0.000015,    "out": 0.000075},
    "claude-opus-4-5":       {"in": 0.000015,    "out": 0.000075},
    "claude-sonnet-4":       {"in": 0.000003,    "out": 0.000015},
    "claude-sonnet-4-5":     {"in": 0.000003,    "out": 0.000015},
    "claude-haiku-4":        {"in": 0.00000025,  "out": 0.00000125},
    "claude-haiku-4-5":      {"in": 0.00000025,  "out": 0.00000125},
    "claude-3-5-sonnet-20241022": {"in": 0.000003, "out": 0.000015},
    "claude-3-5-haiku-20241022":  {"in": 0.0000008, "out": 0.000004},
    "claude-3-opus-20240229":     {"in": 0.000015,  "out": 0.000075},

    # ── Google ──────────────────────────────────────────────────────────────
    "gemini-1.5-pro":        {"in": 0.00000125,  "out": 0.000005},
    "gemini-1.5-flash":      {"in": 0.000000075, "out": 0.0000003},
    "gemini-2.0-flash":      {"in": 0.0000001,   "out": 0.0000004},
    "gemini-2.0-flash-lite": {"in": 0.000000075, "out": 0.0000003},
    "gemini-2.5-pro":        {"in": 0.00000125,  "out": 0.000010},
    "gemini-2.5-flash":      {"in": 0.0000003,   "out": 0.0000025},

    # ── Mistral ─────────────────────────────────────────────────────────────
    "mistral-large":         {"in": 0.000002,    "out": 0.000006},
    "mistral-medium":        {"in": 0.0000027,   "out": 0.0000081},
    "mistral-small":         {"in": 0.000001,    "out": 0.000003},
    "codestral":             {"in": 0.000001,    "out": 0.000003},

    # ── Cohere ──────────────────────────────────────────────────────────────
    "command-r-plus":        {"in": 0.000003,    "out": 0.000015},
    "command-r":             {"in": 0.0000005,   "out": 0.0000015},

    # ── Fallback ─────────────────────────────────────────────────────────────
    "unknown":               {"in": 0.000001,    "out": 0.000002},
}


def _normalise_model(model: str) -> str:
    """
    Normalise a model string to the canonical key in MODEL_PRICING.

    Handles common prefixes / aliases so that e.g.
    "openai/gpt-4o" maps to "gpt-4o".
    """
    model = model.lower().strip()
    # Strip provider prefixes like "openai/", "anthropic/", "google/"
    for prefix in ("openai/", "anthropic/", "google/", "mistral/", "cohere/"):
        if model.startswith(prefix):
            model = model[len(prefix):]
    return model


def calculate_cost(
    model: str,
    tokens_in: int,
    tokens_out: int,
) -> float:
    """
    Calculate the USD cost of an LLM call.

    Args:
        model:      Model identifier string (e.g. "gpt-4o").
        tokens_in:  Number of prompt tokens.
        tokens_out: Number of completion tokens.

    Returns:
        Cost in USD, rounded to 8 decimal places.
        Returns 0.0 if tokens are missing/zero.
    """
    if not model or tokens_in is None or tokens_out is None:
        return 0.0

    key = _normalise_model(model)
    pricing = MODEL_PRICING.get(key, MODEL_PRICING["unknown"])

    cost = (tokens_in * pricing["in"]) + (tokens_out * pricing["out"])
    return round(cost, 8)


def get_model_pricing(model: str) -> Tuple[float, float]:
    """Return (price_per_input_token, price_per_output_token) for a model."""
    key = _normalise_model(model)
    p = MODEL_PRICING.get(key, MODEL_PRICING["unknown"])
    return p["in"], p["out"]
