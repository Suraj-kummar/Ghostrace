"""
ghostrace.backend.utils
~~~~~~~~~~~~~~~~~~~~~~~~
Shared utility helpers used across the backend.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import string
from datetime import datetime, timezone


def utcnow() -> datetime:
    """Return current UTC time (timezone-aware). Use instead of datetime.utcnow()."""
    return datetime.now(timezone.utc)


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token of `length` bytes (hex-encoded)."""
    return secrets.token_hex(length)


def constant_time_compare(a: str, b: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(
        hashlib.sha256(a.encode()).digest(),
        hashlib.sha256(b.encode()).digest(),
    )


def slugify(text: str, max_length: int = 60) -> str:
    """Convert arbitrary text to a URL-safe lowercase slug."""
    allowed = string.ascii_lowercase + string.digits + "-"
    slug = text.lower().replace(" ", "-")
    slug = "".join(c for c in slug if c in allowed)
    # Collapse consecutive dashes
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:max_length]


def mask_api_key(key: str, visible: int = 8) -> str:
    """Return a masked version of an API key, e.g. gr_abc123••••••••."""
    if len(key) <= visible:
        return key
    return f"{key[:visible]}{'•' * min(12, len(key) - visible)}"
