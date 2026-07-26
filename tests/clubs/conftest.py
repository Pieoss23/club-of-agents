from __future__ import annotations

from pathlib import Path

from clubs.initializer import InitAnswers


def make_init_answers(root: Path, **overrides: object) -> InitAnswers:
    """Build InitAnswers with sensible defaults (pattern 1), overridable per test."""
    values: dict[str, object] = {
        "club_name": "Example Club",
        "repository_root": root,
        "main_branch": "main",
    }
    values.update(overrides)
    return InitAnswers(**values)  # type: ignore[arg-type]
