from __future__ import annotations

from pathlib import Path

import pytest

from clubs import tasks
from clubs.initializer import initialize_club

from conftest import make_init_answers as answers


def test_create_task_is_schema_valid_and_in_backlog(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add greet()", objective="Add a greet(name) function with tests.")
    assert task["id"] == "TASK-001"
    assert task["status"] == "backlog"
    assert (tmp_path / "tasks/backlog/TASK-001.json").is_file()


def test_next_task_id_increments_across_stages(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    first = tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add A", objective="First task objective.")
    tasks.move_task(tmp_path, first["id"], from_stage="backlog", to_stage="done")
    assert tasks.next_task_id(tmp_path) == "TASK-002"


def test_move_task_returns_none_when_source_already_gone(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add A", objective="First task objective.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="active")
    result = tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="active")
    assert result is None


def test_find_task_filters_by_owner(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add A", objective="First task objective.")
    task["owner"] = {"agent_id": "developer", "role": "developer", "branch": "unavailable-not-a-git-worktree"}
    tasks.save_task(tmp_path / "tasks/backlog" / f"{task['id']}.json", task)
    assert tasks.find_task(tmp_path, "backlog", owner="developer") is not None
    assert tasks.find_task(tmp_path, "backlog", owner="reviewer") is None


def test_create_task_rejects_invalid_priority(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    with pytest.raises(tasks.TaskError):
        tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add A", objective="First task objective.", priority="urgent")


def test_list_tasks_filters_by_stage_and_lists_all(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    first = tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add A", objective="First task objective.")
    second = tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add B", objective="Second task objective.")
    tasks.move_task(tmp_path, second["id"], from_stage="backlog", to_stage="active")
    assert [task["id"] for task in tasks.list_tasks(tmp_path, "backlog")] == [first["id"]]
    assert [task["id"] for task in tasks.list_tasks(tmp_path, "active")] == [second["id"]]
    assert {task["id"] for task in tasks.list_tasks(tmp_path)} == {first["id"], second["id"]}


def test_find_task_by_id_locates_task_in_any_stage(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    task = tasks.create_task(tmp_path, mission_id="MISSION-001", title="Add A", objective="First task objective.")
    tasks.move_task(tmp_path, task["id"], from_stage="backlog", to_stage="review")
    found = tasks.find_task_by_id(tmp_path, task["id"])
    assert found is not None
    stage, found_task = found
    assert stage == "review"
    assert found_task["id"] == task["id"]
    assert tasks.find_task_by_id(tmp_path, "TASK-999") is None
