from __future__ import annotations

import yaml
from typer.testing import CliRunner

from clubs import __version__
from clubs.cli import app


runner = CliRunner()


def test_help_is_available() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output.lower()


def test_version_is_available() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_init_wizard_creates_club(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["init"],
        input="Example Club\n1\n.\nmain\n1\n4\nplanner\ndeveloper\nreviewer\ncoordinator\n1\n",
    )
    assert result.exit_code == 0, result.output
    assert (tmp_path / ".clubs/club.yaml").is_file()
    assert "created successfully" in result.output


def test_init_wizard_supports_master_workers_pattern(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        ["init"],
        input="Example Club\n1\n.\nmain\n2\n3\n1\n",
    )
    assert result.exit_code == 0, result.output
    config = yaml.safe_load((tmp_path / ".clubs/club.yaml").read_text(encoding="utf-8"))
    assert config["workflow"]["pattern"] == "master-workers"
    assert set(config["agents"]) == {"master", "worker-1", "worker-2", "worker-3"}


def test_task_create_list_show_end_to_end(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    init_result = runner.invoke(
        app, ["init"],
        input="Example Club\n1\n.\nmain\n1\n4\nplanner\ndeveloper\nreviewer\ncoordinator\n1\n",
    )
    assert init_result.exit_code == 0, init_result.output

    mission_result = runner.invoke(
        app, ["mission", "create"],
        input="Add greet()\nAdd a greet(name) function with tests.\n\n",
    )
    assert mission_result.exit_code == 0, mission_result.output

    task_result = runner.invoke(
        app, ["task", "create"],
        input="\nAdd greet() task\nImplement greet(name) with tests.\n\n",
    )
    assert task_result.exit_code == 0, task_result.output
    assert "created in backlog" in task_result.output

    list_result = runner.invoke(app, ["task", "list"])
    assert list_result.exit_code == 0, list_result.output
    assert "TASK-001" in list_result.output
    assert "backlog" in list_result.output

    show_result = runner.invoke(app, ["task", "show", "TASK-001"])
    assert show_result.exit_code == 0, show_result.output
    assert "TASK-001" in show_result.output


def test_task_show_reports_unknown_id(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["init"],
        input="Example Club\n1\n.\nmain\n1\n4\nplanner\ndeveloper\nreviewer\ncoordinator\n1\n",
    )
    result = runner.invoke(app, ["task", "show", "TASK-999"])
    assert result.exit_code == 1
    assert "not found" in result.output


def test_task_cleanup_reports_nothing_when_no_worktrees_exist(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    runner.invoke(
        app, ["init"],
        input="Example Club\n1\n.\nmain\n1\n4\nplanner\ndeveloper\nreviewer\ncoordinator\n1\n",
    )
    result = runner.invoke(app, ["task", "cleanup", "--yes"])
    assert result.exit_code == 0, result.output
    assert "No worktrees to clean up" in result.output
