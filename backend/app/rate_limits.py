"""
ghostrace — project-level rate limit constants.

These constants centralise the per-plan request rate limits
so they can be referenced by both the API layer and the SDK.
"""
from __future__ import annotations

# Max requests per minute per API key (per plan)
RATE_LIMITS: dict[str, int] = {
    "free":       60,
    "pro":        600,
    "team":       3000,
    "enterprise": -1,   # unlimited
}


def get_rate_limit(plan: str) -> int:
    """Return the per-minute ingest rate limit for a given plan name."""
    return RATE_LIMITS.get(plan.lower(), RATE_LIMITS["free"])
