"""Warn-only allowed/forbidden path checking for changed files in a task's worktree.

Never raises: callers record the returned violations (notes, events) but always
let the workflow transition proceed, per this project's confirmed "no agent may
silently expand its scope, but a violation gets flagged rather than blocking".
"""

from __future__ import annotations

import fnmatch


def check(changed_paths: list[str], allowed: list[str], forbidden: list[str]) -> list[str]:
    """Return human-readable violation messages for changed_paths; empty if clean."""
    violations = []
    for path in changed_paths:
        if any(fnmatch.fnmatch(path, pattern) for pattern in forbidden):
            violations.append(f"{path} matches a forbidden path pattern")
        elif allowed and not any(fnmatch.fnmatch(path, pattern) for pattern in allowed):
            violations.append(f"{path} is not covered by any allowed path pattern")
    return violations
