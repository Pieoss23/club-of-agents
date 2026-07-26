from __future__ import annotations

import json
from pathlib import Path

from clubs import runtime, tasks, workflow
from clubs.initializer import initialize_club
from clubs.missions import create_mission

from conftest import make_init_answers as answers


def _setup_club_with_mission(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")


def test_eligible_assignee_skips_busy_agents(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    agents = runtime.load_agents(tmp_path)
    assert workflow.eligible_assignee(tmp_path, agents) == "developer"
    runtime.write_state(tmp_path, "developer", current_task_id="TASK-001")
    assert workflow.eligible_assignee(tmp_path, agents) is None


def test_decompose_mission_creates_task_and_activates_mission(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    mission_path = tmp_path / ".clubs/missions/MISSION-001.json"
    mission = json.loads(mission_path.read_text(encoding="utf-8"))
    task = workflow.decompose_mission(tmp_path, "planner", mission_path, mission, title="Add greet()", objective="Add a greet(name) function with tests.")
    assert task["id"] == "TASK-001"
    assert (tmp_path / "tasks/backlog/TASK-001.json").is_file()
    updated_mission = json.loads(mission_path.read_text(encoding="utf-8"))
    assert updated_mission["status"] == "active"
    assert updated_mission["tasks"] == ["TASK-001"]


def test_assign_task_moves_backlog_to_active_and_writes_assignee_state(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    moved = workflow.assign_task(tmp_path, "coordinator", task, "developer", "developer")
    assert moved == tmp_path / "tasks/active/TASK-001.json"
    assert not (tmp_path / "tasks/backlog/TASK-001.json").exists()
    state = runtime.read_state(tmp_path, "developer")
    assert state.status == "assigned"
    assert state.current_task_id == "TASK-001"


def test_assign_task_returns_none_when_source_already_gone(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="active")
    assert workflow.assign_task(tmp_path, "coordinator", task, "developer", "developer") is None


def test_submit_for_review_moves_active_to_review(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="active")
    moved = workflow.submit_for_review(tmp_path, "developer", task)
    assert moved == tmp_path / "tasks/review/TASK-001.json"


def test_approve_review_sets_flag_without_moving_file(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="review")
    workflow.approve_review(tmp_path, "reviewer", task)
    assert (tmp_path / "tasks/review/TASK-001.json").is_file()
    saved = tasks.load_task(tmp_path / "tasks/review/TASK-001.json")
    assert saved["review_approved"] is True


def test_integrate_moves_review_to_done(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="review")
    moved = workflow.integrate(tmp_path, "coordinator", task)
    assert moved == tmp_path / "tasks/done/TASK-001.json"
    saved = tasks.load_task(moved)
    assert saved["status"] == "done"


def test_integrate_returns_none_when_source_already_gone(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="review")
    tasks.move_task(tmp_path, task["id"], from_stage="review", to_stage="done")
    assert workflow.integrate(tmp_path, "coordinator", task) is None
