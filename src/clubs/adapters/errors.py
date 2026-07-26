"""Shared error type for every real (subprocess-invoking) provider adapter."""

from __future__ import annotations


class ProviderError(RuntimeError):
    """Raised on a subprocess failure, timeout, or unparsable provider output.

    Callers (runtime.run_agent_tick) catch this per-capability so one bad
    provider call never crashes the whole poll loop.
    """
