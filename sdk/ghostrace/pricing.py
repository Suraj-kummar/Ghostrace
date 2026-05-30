"""
ghostrace.pricing
~~~~~~~~~~~~~~~~~
Built-in model pricing table and cost calculation helpers.

Prices are per-token (USD).  All values sourced from official provider
pricing pages as of May 2026 — update this table as prices change.
"""
from __future__ import annotations
from typing import Dict, Tuple
MODEL_PRICING: Dict[str, Dict[str, float]] = {'gpt-4o': {'in': 2.5e-06, 'out': 1e-05}, 'gpt-4o-2024-08-06': {'in': 2.5e-06, 'out': 1e-05}, 'gpt-4o-2024-05-13': {'in': 5e-06, 'out': 1.5e-05}, 'gpt-4o-mini': {'in': 1.5e-07, 'out': 6e-07}, 'gpt-4o-mini-2024-07-18': {'in': 1.5e-07, 'out': 6e-07}, 'gpt-4-turbo': {'in': 1e-05, 'out': 3e-05}, 'gpt-4-turbo-2024-04-09': {'in': 1e-05, 'out': 3e-05}, 'gpt-4': {'in': 3e-05, 'out': 6e-05}, 'gpt-3.5-turbo': {'in': 5e-07, 'out': 1.5e-06}, 'gpt-3.5-turbo-0125': {'in': 5e-07, 'out': 1.5e-06}, 'o1': {'in': 1.5e-05, 'out': 6e-05}, 'o1-mini': {'in': 3e-06, 'out': 1.2e-05}, 'o3': {'in': 1e-05, 'out': 4e-05}, 'o3-mini': {'in': 1.1e-06, 'out': 4.4e-06}, 'o4-mini': {'in': 1.1e-06, 'out': 4.4e-06}, 'claude-opus-4': {'in': 1.5e-05, 'out': 7.5e-05}, 'claude-opus-4-5': {'in': 1.5e-05, 'out': 7.5e-05}, 'claude-sonnet-4': {'in': 3e-06, 'out': 1.5e-05}, 'claude-sonnet-4-5': {'in': 3e-06, 'out': 1.5e-05}, 'claude-haiku-4': {'in': 2.5e-07, 'out': 1.25e-06}, 'claude-haiku-4-5': {'in': 2.5e-07, 'out': 1.25e-06}, 'claude-3-5-sonnet-20241022': {'in': 3e-06, 'out': 1.5e-05}, 'claude-3-5-haiku-20241022': {'in': 8e-07, 'out': 4e-06}, 'claude-3-opus-20240229': {'in': 1.5e-05, 'out': 7.5e-05}, 'gemini-1.5-pro': {'in': 1.25e-06, 'out': 5e-06}, 'gemini-1.5-flash': {'in': 7.5e-08, 'out': 3e-07}, 'gemini-2.0-flash': {'in': 1e-07, 'out': 4e-07}, 'gemini-2.0-flash-lite': {'in': 7.5e-08, 'out': 3e-07}, 'gemini-2.5-pro': {'in': 1.25e-06, 'out': 1e-05}, 'gemini-2.5-flash': {'in': 3e-07, 'out': 2.5e-06}, 'mistral-large': {'in': 2e-06, 'out': 6e-06}, 'mistral-medium': {'in': 2.7e-06, 'out': 8.1e-06}, 'mistral-small': {'in': 1e-06, 'out': 3e-06}, 'codestral': {'in': 1e-06, 'out': 3e-06}, 'command-r-plus': {'in': 3e-06, 'out': 1.5e-05}, 'command-r': {'in': 5e-07, 'out': 1.5e-06}, 'unknown': {'in': 1e-06, 'out': 2e-06}}

def _normalise_model(model: str) -> str:
    pass

def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pass

def get_model_pricing(model: str) -> Tuple[float, float]:
    pass