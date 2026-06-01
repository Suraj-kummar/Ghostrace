"""
Tests for ghostrace.pricing.

Covers:
  - Known models produce correct cost
  - Unknown model uses fallback pricing
  - Normalisation of provider-prefixed model names
  - Zero tokens → zero cost
  - None/empty model → zero cost (graceful)
"""
from __future__ import annotations

import pytest

from ghostrace.pricing import (
    MODEL_PRICING,
    calculate_cost,
    get_model_pricing,
    _normalise_model,
)


class TestCalculateCost:
    def test_gpt4o_cost(self):
        """gpt-4o: in=0.0000025/tok, out=0.000010/tok"""
        # 1000 in, 500 out
        expected = (1000 * 0.0000025) + (500 * 0.000010)
        result = calculate_cost("gpt-4o", 1000, 500)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_gpt4o_mini_cost(self):
        expected = (200 * 0.00000015) + (100 * 0.0000006)
        result = calculate_cost("gpt-4o-mini", 200, 100)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_claude_opus_cost(self):
        expected = (500 * 0.000015) + (200 * 0.000075)
        result = calculate_cost("claude-opus-4", 500, 200)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_gemini_flash_cost(self):
        expected = (1000 * 0.000000075) + (500 * 0.0000003)
        result = calculate_cost("gemini-1.5-flash", 1000, 500)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_unknown_model_uses_fallback(self):
        """Any unrecognised model name must use the 'unknown' fallback pricing."""
        result = calculate_cost("totally-made-up-model-v99", 1000, 500)
        expected = (1000 * 0.000001) + (500 * 0.000002)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_zero_tokens_returns_zero(self):
        assert calculate_cost("gpt-4o", 0, 0) == 0.0

    def test_empty_model_returns_zero(self):
        assert calculate_cost("", 100, 50) == 0.0

    def test_none_tokens_returns_zero(self):
        assert calculate_cost("gpt-4o", None, None) == 0.0  # type: ignore[arg-type]

    def test_result_is_rounded_to_8_decimals(self):
        result = calculate_cost("gpt-4o", 1, 1)
        # Should not have more than 8 decimal places
        assert result == round(result, 8)


class TestNormaliseModel:
    def test_strips_openai_prefix(self):
        assert _normalise_model("openai/gpt-4o") == "gpt-4o"

    def test_strips_anthropic_prefix(self):
        assert _normalise_model("anthropic/claude-opus-4") == "claude-opus-4"

    def test_strips_google_prefix(self):
        assert _normalise_model("google/gemini-1.5-pro") == "gemini-1.5-pro"

    def test_lowercases(self):
        assert _normalise_model("GPT-4O") == "gpt-4o"

    def test_strips_whitespace(self):
        assert _normalise_model("  gpt-4o  ") == "gpt-4o"

    def test_no_prefix_unchanged(self):
        assert _normalise_model("gpt-4o-mini") == "gpt-4o-mini"


class TestGetModelPricing:
    def test_returns_tuple_for_known_model(self):
        price_in, price_out = get_model_pricing("gpt-4o")
        assert price_in == MODEL_PRICING["gpt-4o"]["in"]
        assert price_out == MODEL_PRICING["gpt-4o"]["out"]

    def test_returns_fallback_for_unknown_model(self):
        price_in, price_out = get_model_pricing("nonexistent")
        assert price_in == MODEL_PRICING["unknown"]["in"]
        assert price_out == MODEL_PRICING["unknown"]["out"]


class TestPricingTable:
    def test_all_entries_have_required_keys(self):
        for model, pricing in MODEL_PRICING.items():
            assert "in" in pricing, f"{model} missing 'in'"
            assert "out" in pricing, f"{model} missing 'out'"
            assert isinstance(pricing["in"], float), f"{model}['in'] not float"
            assert isinstance(pricing["out"], float), f"{model}['out'] not float"
            assert pricing["in"] > 0, f"{model}['in'] not positive"
            assert pricing["out"] > 0, f"{model}['out'] not positive"
