"""Thin subprocess wrapper around git worktree/branch/commit mechanics.

Every function here degrades by raising GitError -- callers (workflow.py) decide
whether a failure is fatal or just means "isolation isn't available here."
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    """Raised when a git operation fails or the target isn't a usable git repo."""


@dataclass(frozen=True)
class WorktreeInfo:
    branch: str
    path: Path


def _run_git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def is_git_repo(root: Path) -> bool:
    result = _run_git(root, "rev-parse", "--is-inside-work-tree")
    return result.returncode == 0 and result.stdout.strip() == "true"


def _has_remote(root: Path, name: str = "origin") -> bool:
    result = _run_git(root, "remote")
    return name in result.stdout.split()


def slugify(text: str, *, max_length: int = 30) -> str:
    """Lowercase, hyphen-separated, branch-safe fragment of a task title."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_length].rstrip("-") or "task"


def create_worktree(root: Path, *, role: str, task_id: str, task_title: str, base_branch: str) -> WorktreeInfo:
    """Create a sibling worktree (../<repo-name>-<role>-<task-id>) on a new agent branch."""
    if not is_git_repo(root):
        raise GitError(f"'{root}' is not a git repository.")

    branch = f"agent/{role}/{task_id}-{slugify(task_title)}"
    path = root.parent / f"{root.name}-{role}-{task_id}"

    base_ref = base_branch
    if _has_remote(root):
        fetch = _run_git(root, "fetch", "origin")
        if fetch.returncode == 0:
            base_ref = f"origin/{base_branch}"

    result = _run_git(root, "worktree", "add", str(path), "-b", branch, base_ref)
    if result.returncode != 0:
        raise GitError(f"git worktree add failed: {result.stderr.strip()}")
    return WorktreeInfo(branch=branch, path=path)


def remove_worktree(root: Path, path: Path) -> None:
    result = _run_git(root, "worktree", "remove", str(path), "--force")
    if result.returncode != 0:
        raise GitError(f"git worktree remove failed: {result.stderr.strip()}")


def delete_branch(root: Path, branch: str) -> None:
    result = _run_git(root, "branch", "-D", branch)
    if result.returncode != 0:
        raise GitError(f"git branch -D failed: {result.stderr.strip()}")


def changed_paths(worktree_path: Path, base_ref: str) -> list[str]:
    result = _run_git(worktree_path, "diff", "--name-only", base_ref)
    if result.returncode != 0:
        raise GitError(f"git diff failed: {result.stderr.strip()}")
    return [line for line in result.stdout.splitlines() if line]


def diff_text(worktree_path: Path, base_ref: str) -> str:
    """Full unified diff against base_ref, for feeding a reviewer prompt."""
    result = _run_git(worktree_path, "diff", base_ref)
    if result.returncode != 0:
        raise GitError(f"git diff failed: {result.stderr.strip()}")
    return result.stdout


def commit_all(worktree_path: Path, message: str) -> str | None:
    """Stage and commit everything in the worktree. Returns the new sha, or None if there
    was nothing to commit. Sets a repo-local identity first only if one isn't already set,
    so this also works unattended in a throwaway test/demo repo."""
    identity = _run_git(worktree_path, "config", "user.email")
    if not identity.stdout.strip():
        _run_git(worktree_path, "config", "user.email", "agent@club.local")
        _run_git(worktree_path, "config", "user.name", "Club Agent")

    _run_git(worktree_path, "add", "-A")
    commit = _run_git(worktree_path, "commit", "-m", message)
    if commit.returncode != 0:
        return None
    rev = _run_git(worktree_path, "rev-parse", "HEAD")
    if rev.returncode != 0:
        raise GitError(f"git rev-parse failed: {rev.stderr.strip()}")
    return rev.stdout.strip()
