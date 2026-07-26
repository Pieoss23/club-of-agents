"""End-to-end acceptance coverage for the documented safe ``club`` workflow."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from clubs import git_ops, runtime
from clubs.adapters.dummy import DummyProvider
from clubs.cli import app


runner = CliRunner()


def test_documented_dummy_workflow_completes_with_git_audit_artifacts(
    git_repo: Path, monkeypatch
) -> None:
    """Exercise init, validation, mission creation, lifecycle, status and task display.

    The test deliberately uses the ``dummy`` provider: it verifies the safe,
    provider-independent orchestration promised by the quickstart without calling
    a real AI provider or spending credentials.
    """
    monkeypatch.chdir(git_repo)

    init = runner.invoke(
        app,
        ["init"],
        input="Acceptance Club\n1\n.\nmain\n1\n4\nplanner\ndeveloper\nreviewer\ncoordinator\n1\n",
    )
    assert init.exit_code == 0, init.output

    validate = runner.invoke(app, ["validate"])
    assert validate.exit_code == 0, validate.output

    mission = runner.invoke(
        app,
        ["mission", "create"],
        input="Ship greeting\nAdd a greeting implementation with tests.\n\n",
    )
    assert mission.exit_code == 0, mission.output
    assert "MISSION-001" in mission.output

    provider = DummyProvider()
    for agent_id in ("planner", "coordinator", "developer", "reviewer", "coordinator"):
        runtime.run_agent_tick(git_repo, agent_id, provider)

    status = runner.invoke(app, ["status"])
    assert status.exit_code == 0, status.output
    assert "1" in status.output

    task_list = runner.invoke(app, ["task", "list", "--stage", "done"])
    assert task_list.exit_code == 0, task_list.output
    assert "TASK-001" in task_list.output
    assert "done" in task_list.output

    task_show = runner.invoke(app, ["task", "show", "TASK-001"])
    assert task_show.exit_code == 0, task_show.output
    assert "review_approved" in task_show.output

    task_path = git_repo / "tasks/done/TASK-001.json"
    task = json.loads(task_path.read_text(encoding="utf-8"))
    assert task["status"] == "done"
    assert task["review_approved"] is True
    assert task["owner"]["branch"].startswith("agent/developer/TASK-001")
    assert task["audit"]["commits"]
    assert task["audit"]["pull_request"] == "docs/handoffs/TASK-001-pr-draft.md"
    assert (git_repo / task["audit"]["pull_request"]).is_file()
    assert (Path(task["owner"]["worktree"]) / "NOTES.md").is_file()

    events = [json.loads(line) for line in (git_repo / ".clubs/runtime/events/events.jsonl").read_text(encoding="utf-8").splitlines()]
    event_types = {event["type"] for event in events}
    assert {
        "task.created", "worktree.created", "task.assigned", "task.ready_for_review",
        "review.approved", "task.completed",
    } <= event_types

    worktree_path = Path(task["owner"]["worktree"])
    branch = task["owner"]["branch"]

    cleanup = runner.invoke(app, ["task", "cleanup", "--yes"])
    assert cleanup.exit_code == 0, cleanup.output
    assert "Cleaned up TASK-001" in cleanup.output
    assert not worktree_path.exists()
    remaining_branch = git_ops._run_git(git_repo, "branch", "--list", branch)
    assert remaining_branch.stdout.strip() == ""
