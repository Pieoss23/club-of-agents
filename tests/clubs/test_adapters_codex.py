from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from clubs import tasks, workflow
from clubs.adapters.codex import CodexProvider
from clubs.adapters.errors import ProviderError
from clubs.initializer import initialize_club
from clubs.missions import create_mission

from conftest import make_init_answers as answers


def _fake_run(stdout: str, *, returncode: int = 0, stderr: str = ""):
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr=stderr)
    return run


def test_plan_creates_task_from_codex_response(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    reply = json.dumps({"title": "Add greet()", "objective": "Add a greet(name) function with tests."})
    provider = CodexProvider(run=_fake_run(reply))

    provider.plan(tmp_path, "planner")

    assert len(list((tmp_path / "tasks/backlog").glob("TASK-*.json"))) == 1
    assert (tmp_path / "logs/agents/planner/MISSION-001-plan.log").is_file()


def test_plan_raises_provider_error_on_nonzero_exit(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    provider = CodexProvider(run=_fake_run("", returncode=1, stderr="sandbox denied"))
    with pytest.raises(ProviderError):
        provider.plan(tmp_path, "planner")


def test_plan_raises_provider_error_on_missing_binary(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")

    def missing(args, **kwargs):
        raise FileNotFoundError("codex not found")

    provider = CodexProvider(run=missing)
    with pytest.raises(ProviderError):
        provider.plan(tmp_path, "planner")


def test_implement_refuses_when_no_real_worktree(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(tmp_path, "coordinator", task, "developer", "developer")
    provider = CodexProvider(run=_fake_run("done"))
    with pytest.raises(ProviderError):
        provider.implement(tmp_path, "developer")


def test_implement_submits_for_review_when_worktree_is_real(git_repo: Path) -> None:
    initialize_club(answers(git_repo))
    task = tasks.create_task(git_repo, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(git_repo, "coordinator", task, "developer", "developer")
    provider = CodexProvider(run=_fake_run("Implemented the greet function."))

    provider.implement(git_repo, "developer")

    review = list((git_repo / "tasks/review").glob("TASK-*.json"))
    assert len(review) == 1
    saved = tasks.load_task(review[0])
    assert "codex:" in saved["notes"][-1]
    assert (git_repo / "logs/agents/developer" / f"{task['id']}-implement.log").is_file()


def test_review_approves_and_marks_criteria_verified(git_repo: Path) -> None:
    initialize_club(answers(git_repo))
    task = tasks.create_task(git_repo, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(git_repo, "coordinator", task, "developer", "developer")
    tasks.move_task(git_repo, task["id"], from_stage="active", to_stage="review")
    verdict = json.dumps({"approved": True, "findings": []})
    provider = CodexProvider(run=_fake_run(verdict))

    provider.review(git_repo, "reviewer")

    saved = tasks.load_task(git_repo / "tasks/review" / f"{task['id']}.json")
    assert saved["review_approved"] is True
    assert all(c["verified"] for c in saved["acceptance_criteria"])


def test_review_records_findings_without_approving_on_rejection(git_repo: Path) -> None:
    initialize_club(answers(git_repo))
    task = tasks.create_task(git_repo, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(git_repo, "coordinator", task, "developer", "developer")
    tasks.move_task(git_repo, task["id"], from_stage="active", to_stage="review")
    verdict = json.dumps({"approved": False, "findings": ["Missing tests."]})
    provider = CodexProvider(run=_fake_run(verdict))

    provider.review(git_repo, "reviewer")

    assert not (git_repo / "tasks/review" / f"{task['id']}.json").exists()
    saved = tasks.load_task(git_repo / "tasks/active" / f"{task['id']}.json")
    assert saved["review_approved"] is False
    assert any("Missing tests." in note for note in saved["notes"])
