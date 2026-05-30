"""
Shared fixtures for all ghostrace SDK tests.
"""
from __future__ import annotations

import importlib
import sys

import pytest


@pytest.fixture(autouse=True)
def reset_ghostrace():
    """
    Reset all SDK singletons before each test so tests are isolated.

    We use ``importlib.import_module`` for the session submodule to bypass
    the name collision: ``ghostrace.session`` in the package namespace points
    to the exported *function*, not the submodule.  importlib always returns
    the actual module object.
    """
    import ghostrace.collector as _col_mod
    import ghostrace.config as _cfg_mod

    # importlib.import_module always returns the *module*, not any attribute
    # of the same name in the parent package's namespace.
    _sess_mod = importlib.import_module("ghostrace.session")

    # Reset config singleton
    _cfg_mod._INSTANCE = None

    # Reset collector singleton and anonymous session ID
    _col_mod._collector = None
    _col_mod._anon_session_id = None

    # Reset session registry and context-var stack
    _sess_mod._SESSION_REGISTRY.clear()  # type: ignore[attr-defined]
    _sess_mod._SESSION_STACK.set([])     # type: ignore[attr-defined]

    yield

    # Teardown
    _cfg_mod._INSTANCE = None
    _col_mod._collector = None
    _col_mod._anon_session_id = None
    _sess_mod._SESSION_REGISTRY.clear()  # type: ignore[attr-defined]
    _sess_mod._SESSION_STACK.set([])     # type: ignore[attr-defined]

