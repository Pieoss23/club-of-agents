from __future__ import annotations

import json
from pathlib import Path

import pytest

from clubs.initializer import initialize_club
from clubs.missions import MissionError, create_mission, next_mission_id
from clubs.models import Mission

from conftest import make_init_answers as answers


def test_first_mission_gets_sequential_id(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    mission = create_mission(tmp_path, title="Add auth", description="Users must log in.")
    assert mission.id == "MISSION-001"
    assert (tmp_path / ".clubs/missions/MISSION-001.json").is_file()


def test_second_mission_increments_id(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add auth", description="Users must log in.")
    second = create_mission(tmp_path, title="Add billing", description="Users must be billed.")
    assert second.id == "MISSION-002"


def test_invalid_priority_is_rejected(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    with pytest.raises(MissionError):
        create_mission(tmp_path, title="Add auth", description="Users must log in.", priority="urgent")


def test_mission_file_round_trips_through_model(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    create_mission(tmp_path, title="Add auth", description="Users must log in.")
    raw = json.loads((tmp_path / ".clubs/missions/MISSION-001.json").read_text(encoding="utf-8"))
    reloaded = Mission.model_validate(raw)
    assert reloaded.title == "Add auth"


def test_next_mission_id_starts_at_one(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    assert next_mission_id(tmp_path) == "MISSION-001"
