from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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


def _run_git(cwd: Path, *args: str) -> None:
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """A real, minimal git repo on branch 'main' with one commit -- a valid base ref
    for worktree tests, isolated from the user's global git config."""
    _run_git(tmp_path, "init")
    _run_git(tmp_path, "config", "user.email", "test@example.com")
    _run_git(tmp_path, "config", "user.name", "Test")
    (tmp_path / "README.md").write_text("init\n", encoding="utf-8")
    _run_git(tmp_path, "add", "-A")
    _run_git(tmp_path, "commit", "-m", "initial commit")
    _run_git(tmp_path, "branch", "-M", "main")
    return tmp_path
