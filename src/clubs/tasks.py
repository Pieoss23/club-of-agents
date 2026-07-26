"""Task I/O and lifecycle transitions, validated against the bundled task schema."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

import jsonschema

from clubs.models import MISSION_PRIORITIES
from clubs.validator import validate_club

TASK_STAGES = ("backlog", "active", "review", "blocked", "done")
TASK_ID_PATTERN = re.compile(r"^TASK-(\d{3,})$")


class TaskError(RuntimeError):
    """Raised when a task cannot be created or does not match the schema."""


def _schema() -> dict:
    source = resources.files("clubs").joinpath("templates", "task.schema.json")
    return json.loads(source.read_text(encoding="utf-8"))


def next_task_id(root: Path) -> str:
    """Return the next sequential task id, e.g. TASK-001, scanning every stage."""
    highest = 0
    for stage in TASK_STAGES:
        stage_dir = root / "tasks" / stage
        if not stage_dir.is_dir():
            continue
        for path in stage_dir.glob("TASK-*.json"):
            match = TASK_ID_PATTERN.fullmatch(path.stem)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"TASK-{highest + 1:03d}"


def create_task(root: Path, *, mission_id: str, title: str, objective: str, priority: str = "medium") -> dict:
    """Build a schema-valid task dict and write it to tasks/backlog/."""
    result = validate_club(root)
    if not result.ok:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in result.issues)
        raise TaskError(f"Club configuration is invalid. Run 'club validate' for details. {details}")
    if priority not in MISSION_PRIORITIES:
        raise TaskError(f"Priority must be one of {', '.join(MISSION_PRIORITIES)}, got '{priority}'.")

    task = {
        "id": next_task_id(root),
        "title": title,
        "objective": objective,
        "status": "backlog",
        "priority": priority,
        "owner": None,
        "scope": [objective],
        "allowed_paths": ["**"],
        "forbidden_paths": [],
        "acceptance_criteria": [
            {"id": "AC-1", "description": objective, "verified": False, "evidence": None},
        ],
        "required_tests": [],
        "dependencies": [],
        "risk": {"level": "low", "reasons": [], "reviewers": []},
        "audit": {
            "started_at": None, "completed_at": None, "commits": [],
            "pull_request": None, "test_log": None, "handoff": None,
        },
        "notes": [f"Created from {mission_id}."],
    }
    try:
        jsonschema.validate(task, _schema())
    except jsonschema.ValidationError as error:
        raise TaskError(f"Generated task does not match the task schema: {error.message}") from error

    backlog_dir = root / "tasks" / "backlog"
    backlog_dir.mkdir(parents=True, exist_ok=True)
    save_task(backlog_dir / f"{task['id']}.json", task)
    return task


def load_task(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_task(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def move_task(root: Path, task_id: str, *, from_stage: str, to_stage: str) -> Path | None:
    """Atomically move a task file between stage directories.

    Returns the new path, or None if the source is already gone (another
    process claimed it first) instead of raising -- this is the race-safe
    claiming primitive every dummy-provider transition relies on.
    """
    source = root / "tasks" / from_stage / f"{task_id}.json"
    destination = root / "tasks" / to_stage / f"{task_id}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        source.rename(destination)
    except FileNotFoundError:
        return None
    return destination


def find_task(root: Path, stage: str, *, owner: str | None = None) -> dict | None:
    """Return the first task JSON found in a stage, optionally filtered by owner agent id."""
    stage_dir = root / "tasks" / stage
    if not stage_dir.is_dir():
        return None
    for path in sorted(stage_dir.glob("TASK-*.json")):
        task = load_task(path)
        if owner is None:
            return task
        task_owner = task.get("owner") or {}
        if task_owner.get("agent_id") == owner:
            return task
    return None


def list_tasks(root: Path, stage: str | None = None) -> list[dict]:
    """Every task in one stage, or across all stages if stage is None."""
    stages = (stage,) if stage else TASK_STAGES
    result = []
    for current_stage in stages:
        stage_dir = root / "tasks" / current_stage
        if not stage_dir.is_dir():
            continue
        for path in sorted(stage_dir.glob("TASK-*.json")):
            result.append(load_task(path))
    return result


def find_task_by_id(root: Path, task_id: str) -> tuple[str, dict] | None:
    """Return (stage, task) for a task id regardless of which stage it's in, or None."""
    for stage in TASK_STAGES:
        path = root / "tasks" / stage / f"{task_id}.json"
        if path.is_file():
            return stage, load_task(path)
    return None


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
