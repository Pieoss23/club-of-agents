from __future__ import annotations

from pathlib import Path

import pytest

from clubs import git_ops


def test_is_git_repo_true_for_real_repo(git_repo: Path) -> None:
    assert git_ops.is_git_repo(git_repo) is True


def test_is_git_repo_false_for_plain_directory(tmp_path: Path) -> None:
    assert git_ops.is_git_repo(tmp_path) is False


def test_create_worktree_creates_branch_and_sibling_directory(git_repo: Path) -> None:
    info = git_ops.create_worktree(
        git_repo, role="developer", task_id="TASK-001", task_title="Add greet()", base_branch="main",
    )
    assert info.branch == "agent/developer/TASK-001-add-greet"
    assert info.path.is_dir()
    assert info.path.parent == git_repo.parent
    assert (info.path / "README.md").is_file()


def test_create_worktree_raises_when_not_a_git_repo(tmp_path: Path) -> None:
    with pytest.raises(git_ops.GitError):
        git_ops.create_worktree(
            tmp_path, role="developer", task_id="TASK-001", task_title="Add greet()", base_branch="main",
        )


def test_changed_paths_detects_modified_and_new_files(git_repo: Path) -> None:
    info = git_ops.create_worktree(
        git_repo, role="developer", task_id="TASK-001", task_title="Add greet()", base_branch="main",
    )
    (info.path / "README.md").write_text("changed\n", encoding="utf-8")
    (info.path / "new_file.txt").write_text("new\n", encoding="utf-8")
    git_ops._run_git(info.path, "add", "-A")
    git_ops._run_git(info.path, "commit", "-m", "wip")

    changed = git_ops.changed_paths(info.path, "main")
    assert set(changed) == {"README.md", "new_file.txt"}


def test_commit_all_returns_sha_when_something_changed(git_repo: Path) -> None:
    info = git_ops.create_worktree(
        git_repo, role="developer", task_id="TASK-001", task_title="Add greet()", base_branch="main",
    )
    (info.path / "new_file.txt").write_text("new\n", encoding="utf-8")
    sha = git_ops.commit_all(info.path, "add new_file.txt")
    assert sha is not None
    assert len(sha) == 40


def test_commit_all_returns_none_when_nothing_changed(git_repo: Path) -> None:
    info = git_ops.create_worktree(
        git_repo, role="developer", task_id="TASK-001", task_title="Add greet()", base_branch="main",
    )
    assert git_ops.commit_all(info.path, "nothing to commit") is None


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Add greet()", "add-greet"),
        ("Fix bug #42!!", "fix-bug-42"),
        ("A" * 50, "a" * 30),
        ("   ", "task"),
    ],
)
def test_slugify(text: str, expected: str) -> None:
    assert git_ops.slugify(text) == expected


def test_delete_branch_removes_it(git_repo: Path) -> None:
    info = git_ops.create_worktree(
        git_repo, role="developer", task_id="TASK-001", task_title="Add greet()", base_branch="main",
    )
    git_ops.remove_worktree(git_repo, info.path)  # branches can't be deleted while checked out in a worktree

    git_ops.delete_branch(git_repo, info.branch)

    result = git_ops._run_git(git_repo, "branch", "--list", info.branch)
    assert result.stdout.strip() == ""


def test_delete_branch_raises_on_unknown_branch(git_repo: Path) -> None:
    with pytest.raises(git_ops.GitError):
        git_ops.delete_branch(git_repo, "no-such-branch")
