from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from clubs import runtime, tasks
from clubs.adapters.dummy import DummyProvider
from clubs.initializer import initialize_club
from clubs.missions import create_mission

from conftest import make_init_answers as answers


def _setup_club_with_mission(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")


def test_unknown_agent_raises(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    with pytest.raises(runtime.UnknownAgentError):
        runtime.run_agent_tick(tmp_path, "not-a-real-agent", DummyProvider())


def test_planner_tick_creates_one_backlog_task(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    runtime.run_agent_tick(tmp_path, "planner", DummyProvider())
    backlog = list((tmp_path / "tasks/backlog").glob("TASK-*.json"))
    assert len(backlog) == 1
    mission = json.loads((tmp_path / ".clubs/missions/MISSION-001.json").read_text(encoding="utf-8"))
    assert mission["status"] == "active"
    assert mission["tasks"] == [backlog[0].stem]


def test_coordinator_tick_assigns_backlog_task_to_developer(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    runtime.run_agent_tick(tmp_path, "planner", DummyProvider())
    runtime.run_agent_tick(tmp_path, "coordinator", DummyProvider())
    assert not list((tmp_path / "tasks/backlog").glob("TASK-*.json"))
    active = list((tmp_path / "tasks/active").glob("TASK-*.json"))
    assert len(active) == 1
    task = json.loads(active[0].read_text(encoding="utf-8"))
    assert task["owner"]["agent_id"] == "developer"


def test_developer_tick_moves_active_task_to_review(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    runtime.run_agent_tick(tmp_path, "planner", DummyProvider())
    runtime.run_agent_tick(tmp_path, "coordinator", DummyProvider())
    runtime.run_agent_tick(tmp_path, "developer", DummyProvider())
    assert not list((tmp_path / "tasks/active").glob("TASK-*.json"))
    review = list((tmp_path / "tasks/review").glob("TASK-*.json"))
    assert len(review) == 1
    task = json.loads(review[0].read_text(encoding="utf-8"))
    assert all(criterion["verified"] for criterion in task["acceptance_criteria"])


def test_reviewer_tick_approves_without_moving_file(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    runtime.run_agent_tick(tmp_path, "planner", DummyProvider())
    runtime.run_agent_tick(tmp_path, "coordinator", DummyProvider())
    runtime.run_agent_tick(tmp_path, "developer", DummyProvider())
    runtime.run_agent_tick(tmp_path, "reviewer", DummyProvider())
    review = list((tmp_path / "tasks/review").glob("TASK-*.json"))
    assert len(review) == 1
    task = json.loads(review[0].read_text(encoding="utf-8"))
    assert task["review_approved"] is True


def test_full_lifecycle_ends_in_done_and_is_schema_valid(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    provider = DummyProvider()
    for role in ("planner", "coordinator", "developer", "reviewer", "coordinator"):
        runtime.run_agent_tick(tmp_path, role, provider)

    done = list((tmp_path / "tasks/done").glob("TASK-*.json"))
    assert len(done) == 1
    task = json.loads(done[0].read_text(encoding="utf-8"))
    assert task["status"] == "done"

    schema = json.loads((tmp_path / ".clubs/schemas/task.schema.json").read_text(encoding="utf-8"))
    jsonschema.validate(task, schema)


def test_race_lost_move_is_a_no_op_not_an_exception(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    runtime.run_agent_tick(tmp_path, "planner", DummyProvider())
    runtime.run_agent_tick(tmp_path, "coordinator", DummyProvider())
    active = list((tmp_path / "tasks/active").glob("TASK-*.json"))[0]
    task_id = active.stem
    # Simulate another process having already moved this task before this tick runs.
    tasks.move_task(tmp_path, task_id, from_stage="active", to_stage="review")
    # Should not raise even though the file is no longer where implement() expects it mid-flight.
    runtime.run_agent_tick(tmp_path, "developer", DummyProvider())


def test_agent_state_reflects_current_task_immediately_on_assignment(tmp_path: Path) -> None:
    _setup_club_with_mission(tmp_path)
    runtime.run_agent_tick(tmp_path, "planner", DummyProvider())
    runtime.run_agent_tick(tmp_path, "coordinator", DummyProvider())
    # the coordinator pushes assignment into developer's state file directly, so club status
    # shows the handoff even before developer's own process has ticked even once.
    state = runtime.read_state(tmp_path, "developer")
    assert state.status == "assigned"
    assert state.current_task_id is not None


def test_coordinator_does_not_double_assign_a_busy_developer(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    create_mission(tmp_path, title="Add farewell()", description="Add a farewell(name) function with tests.")
    provider = DummyProvider()
    runtime.run_agent_tick(tmp_path, "planner", provider)
    runtime.run_agent_tick(tmp_path, "planner", provider)
    runtime.run_agent_tick(tmp_path, "coordinator", provider)
    runtime.run_agent_tick(tmp_path, "coordinator", provider)
    assert len(list((tmp_path / "tasks/active").glob("TASK-*.json"))) == 1
    assert len(list((tmp_path / "tasks/backlog").glob("TASK-*.json"))) == 1
