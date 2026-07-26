from __future__ import annotations

import json
from pathlib import Path

import pytest

from clubs.initializer import initialize_club
from clubs.status import StatusError, collect_status

from conftest import make_init_answers as answers


def test_fresh_club_reports_all_agents_offline_and_zero_counts(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    status = collect_status(tmp_path)
    assert status.club_name == "Example Club"
    assert status.missions == 0
    assert status.tasks.model_dump() == {"backlog": 0, "active": 0, "review": 0, "blocked": 0, "done": 0}
    assert len(status.agents) == 4
    assert all(agent.state == "offline" for agent in status.agents)


def test_task_files_are_counted_by_stage(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    (tmp_path / "tasks/active/TASK-001.json").write_text("{}", encoding="utf-8")
    (tmp_path / "tasks/backlog/TASK-002.json").write_text("{}", encoding="utf-8")
    status = collect_status(tmp_path)
    assert status.tasks.active == 1
    assert status.tasks.backlog == 1


def test_agent_state_file_is_reflected(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    state_dir = tmp_path / ".clubs/runtime/state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "developer.json").write_text(
        json.dumps({"status": "working", "current_task_id": "TASK-001"}), encoding="utf-8"
    )
    status = collect_status(tmp_path)
    developer = next(agent for agent in status.agents if agent.agent_id == "developer")
    assert developer.state == "working"
    assert developer.current_task_id == "TASK-001"


def test_invalid_club_raises_status_error(tmp_path: Path) -> None:
    with pytest.raises(StatusError):
        collect_status(tmp_path)
