from __future__ import annotations

from pathlib import Path

from clubs import patterns
from clubs.initializer import initialize_club
from clubs.validator import validate_club

from conftest import make_init_answers as answers


def test_freshly_initialized_club_is_valid(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    result = validate_club(tmp_path)
    assert result.ok, result.issues


def test_missing_club_yaml_is_reported(tmp_path: Path) -> None:
    result = validate_club(tmp_path)
    assert not result.ok
    assert any(issue.path == ".clubs/club.yaml" for issue in result.issues)


def test_corrupt_yaml_is_reported(tmp_path: Path) -> None:
    club_yaml = tmp_path / ".clubs/club.yaml"
    club_yaml.parent.mkdir(parents=True)
    club_yaml.write_text("club: [unterminated", encoding="utf-8")
    result = validate_club(tmp_path)
    assert not result.ok
    assert "Invalid YAML" in result.issues[0].message


def test_missing_master_contract_file_is_reported(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    (tmp_path / "MASTER_CONTRACT.md").unlink()
    result = validate_club(tmp_path)
    assert any(issue.path == "MASTER_CONTRACT.md" for issue in result.issues)


def test_unknown_workflow_pattern_is_reported(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    club_yaml = tmp_path / ".clubs/club.yaml"
    club_yaml.write_text(club_yaml.read_text(encoding="utf-8").replace(
        "pattern: planner-developer-reviewer-coordinator", "pattern: not-a-real-pattern"
    ), encoding="utf-8")
    result = validate_club(tmp_path)
    assert any(issue.path == "workflow.pattern" for issue in result.issues)


def test_master_workers_pattern_is_valid(tmp_path: Path) -> None:
    initialize_club(answers(
        tmp_path, workflow_pattern=patterns.MASTER_WORKERS, agents=patterns.master_workers(2),
    ))
    result = validate_club(tmp_path)
    assert result.ok, result.issues


def test_architect_frontend_backend_reviewer_pattern_is_valid(tmp_path: Path) -> None:
    initialize_club(answers(
        tmp_path, workflow_pattern=patterns.ARCHITECT_FRONTEND_BACKEND_REVIEWER,
        agents=patterns.architect_frontend_backend_reviewer(),
    ))
    result = validate_club(tmp_path)
    assert result.ok, result.issues


def test_swarm_by_component_pattern_is_valid(tmp_path: Path) -> None:
    initialize_club(answers(
        tmp_path, workflow_pattern=patterns.SWARM_BY_COMPONENT,
        agents=patterns.swarm_by_component(("auth", "billing")),
    ))
    result = validate_club(tmp_path)
    assert result.ok, result.issues


def test_custom_pattern_is_valid(tmp_path: Path) -> None:
    initialize_club(answers(
        tmp_path, workflow_pattern=patterns.CUSTOM,
        agents=patterns.custom((("lead", ("plan", "merge")),)),
    ))
    result = validate_club(tmp_path)
    assert result.ok, result.issues


def test_missing_required_directory_is_reported(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    (tmp_path / "tasks/backlog").rmdir()
    result = validate_club(tmp_path)
    assert any(issue.path == "tasks/backlog" for issue in result.issues)
