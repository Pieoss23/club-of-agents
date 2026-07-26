from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from clubs import tasks, workflow
from clubs.adapters.claude import ClaudeProvider
from clubs.adapters.errors import ProviderError
from clubs.initializer import initialize_club
from clubs.missions import create_mission

from conftest import make_init_answers as answers


def _claude_json(result_text: str) -> str:
    return json.dumps({"result": result_text})


def _fake_run(stdout: str, *, returncode: int = 0, stderr: str = ""):
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, returncode, stdout=stdout, stderr=stderr)
    return run


def test_plan_creates_task_from_claude_response(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    reply = json.dumps({"title": "Add greet()", "objective": "Add a greet(name) function with tests."})
    provider = ClaudeProvider(run=_fake_run(_claude_json(reply)))

    provider.plan(tmp_path, "planner")

    backlog = list((tmp_path / "tasks/backlog").glob("TASK-*.json"))
    assert len(backlog) == 1
    assert (tmp_path / "logs/agents/planner/MISSION-001-plan.log").is_file()


def test_plan_is_a_no_op_when_no_pending_mission(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    provider = ClaudeProvider(run=_fake_run(_claude_json("{}")))
    provider.plan(tmp_path, "planner")  # should not raise, should not call run
    assert not list((tmp_path / "tasks/backlog").glob("TASK-*.json"))


def test_plan_raises_provider_error_on_non_json_reply(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    provider = ClaudeProvider(run=_fake_run(_claude_json("not json at all")))
    with pytest.raises(ProviderError):
        provider.plan(tmp_path, "planner")


def test_plan_raises_provider_error_on_nonzero_exit(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    provider = ClaudeProvider(run=_fake_run("", returncode=1, stderr="boom"))
    with pytest.raises(ProviderError):
        provider.plan(tmp_path, "planner")


def test_plan_raises_provider_error_on_timeout(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")

    def timeout_run(args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args, timeout=1)

    provider = ClaudeProvider(run=timeout_run)
    with pytest.raises(ProviderError):
        provider.plan(tmp_path, "planner")


def test_implement_refuses_when_no_real_worktree(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(tmp_path, "coordinator", task, "developer", "developer")  # not a git repo -> placeholder
    provider = ClaudeProvider(run=_fake_run(_claude_json("done")))
    with pytest.raises(ProviderError):
        provider.implement(tmp_path, "developer")


def test_implement_submits_for_review_when_worktree_is_real(git_repo: Path) -> None:
    initialize_club(answers(git_repo))
    task = tasks.create_task(git_repo, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(git_repo, "coordinator", task, "developer", "developer")
    provider = ClaudeProvider(run=_fake_run(_claude_json("Implemented the greet function.")))

    provider.implement(git_repo, "developer")

    review = list((git_repo / "tasks/review").glob("TASK-*.json"))
    assert len(review) == 1
    saved = tasks.load_task(review[0])
    assert "claude:" in saved["notes"][-1]
    assert (git_repo / "logs/agents/developer" / f"{task['id']}-implement.log").is_file()


def test_review_approves_and_marks_criteria_verified(git_repo: Path) -> None:
    initialize_club(answers(git_repo))
    task = tasks.create_task(git_repo, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    workflow.assign_task(git_repo, "coordinator", task, "developer", "developer")
    tasks.move_task(git_repo, task["id"], from_stage="active", to_stage="review")
    verdict = json.dumps({"approved": True, "findings": []})
    provider = ClaudeProvider(run=_fake_run(_claude_json(verdict)))

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
    provider = ClaudeProvider(run=_fake_run(_claude_json(verdict)))

    provider.review(git_repo, "reviewer")

    assert not (git_repo / "tasks/review" / f"{task['id']}.json").exists()
    saved = tasks.load_task(git_repo / "tasks/active" / f"{task['id']}.json")
    assert saved["review_approved"] is False
    assert any("Missing tests." in note for note in saved["notes"])
