"""
ghostrace.config
~~~~~~~~~~~~~~~~
Global configuration singleton. Set once via ghostrace.init() and read
everywhere else through get_config().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Bump this when the SDK wire format changes
SDK_VERSION = "0.3.0"

_INSTANCE: Optional["GhostraceConfig"] = None


@dataclass
class GhostraceConfig:
    api_key: str = ""
    project: str = "default"
    base_url: str = "https://api.ghostrace.dev"
    debug: bool = False
    # When True the SDK only writes locally — useful for offline dev / testing
    local_only: bool = False
    # Max events to buffer in memory before flushing
    max_buffer_size: int = 100
    # Retry configuration
    retry_attempts: int = 3
    retry_backoff_base: float = 1.0  # seconds; doubles on each attempt
    # Maximum number of tag key/value pairs per session
    max_tags: int = 20

    def is_configured(self) -> bool:
        return bool(self.api_key) or self.local_only

    @property
    def sdk_user_agent(self) -> str:
        return f"ghostrace-python/{SDK_VERSION}"


def init(
    api_key: str = "",
    project: str = "default",
    base_url: str = "https://api.ghostrace.dev",
    debug: bool = False,
    local_only: bool = False,
    retry_attempts: int = 3,
    retry_backoff_base: float = 1.0,
    max_tags: int = 20,
) -> GhostraceConfig:
    """
    Initialise the Ghostrace SDK. Call once at application startup.

    Args:
        api_key:             Your Ghostrace API key (starts with ``gr_``).
        project:             Project name — must match a project in the dashboard.
        base_url:            Override the backend URL (useful for self-hosting).
        debug:               Print verbose SDK internals to stderr.
        local_only:          Skip HTTP entirely; only write to ~/.ghostrace/traces/.
        retry_attempts:      Number of HTTP send retries (default 3).
        retry_backoff_base:  Base delay in seconds between retries (doubles each time).
        max_tags:            Maximum tag key/value pairs per session.
    """
    global _INSTANCE
    _INSTANCE = GhostraceConfig(
        api_key=api_key,
        project=project,
        base_url=base_url.rstrip("/"),
        debug=debug,
        local_only=local_only,
        retry_attempts=retry_attempts,
        retry_backoff_base=retry_backoff_base,
        max_tags=max_tags,
    )
    return _INSTANCE


def get_config() -> GhostraceConfig:
    """Return the current config, creating a default one if init() was never called."""
    global _INSTANCE
    if _INSTANCE is None:
        _INSTANCE = GhostraceConfig()
    return _INSTANCE
