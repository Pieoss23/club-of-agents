from __future__ import annotations

from pathlib import Path

from clubs import runtime, tasks
from clubs.adapters.mechanical import MechanicalAssignMergeMixin, pending_missions
from clubs.initializer import initialize_club
from clubs.missions import create_mission

from conftest import make_init_answers as answers


class _BareMechanicalProvider(MechanicalAssignMergeMixin):
    """Nothing but the shared mechanical capabilities -- proves the extraction
    behaves identically to what DummyProvider used to implement inline."""


def test_assign_matches_backlog_task_to_capable_free_agent(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    provider = _BareMechanicalProvider()
    agents = runtime.load_agents(tmp_path)
    provider.assign(tmp_path, "coordinator", agents)

    assert not (tmp_path / "tasks/backlog" / f"{task['id']}.json").exists()
    active = tasks.load_task(tmp_path / "tasks/active" / f"{task['id']}.json")
    assert active["owner"]["agent_id"] == "developer"


def test_assign_is_a_no_op_when_backlog_is_empty(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    provider = _BareMechanicalProvider()
    agents = runtime.load_agents(tmp_path)
    provider.assign(tmp_path, "coordinator", agents)  # should not raise
    assert not list((tmp_path / "tasks/active").glob("TASK-*.json"))


def test_merge_moves_approved_review_task_to_done(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="review")
    task["review_approved"] = True
    tasks.save_task(tmp_path / "tasks/review" / f"{task['id']}.json", task)

    provider = _BareMechanicalProvider()
    provider.merge(tmp_path, "coordinator")

    assert (tmp_path / "tasks/done" / f"{task['id']}.json").is_file()


def test_merge_is_a_no_op_when_review_task_is_not_yet_approved(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="A task", objective="Do something useful.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="review")

    provider = _BareMechanicalProvider()
    provider.merge(tmp_path, "coordinator")

    assert (tmp_path / "tasks/review" / f"{task['id']}.json").is_file()
    assert not (tmp_path / "tasks/done" / f"{task['id']}.json").exists()


def test_pending_missions_returns_only_unstarted_missions(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add greet()", description="Add a greet(name) function with tests.")
    pending = pending_missions(tmp_path)
    assert len(pending) == 1
    assert pending[0][1]["title"] == "Add greet()"
