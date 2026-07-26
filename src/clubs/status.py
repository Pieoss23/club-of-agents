"""Collects a point-in-time snapshot of a club's agents, tasks, and missions."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from pydantic import BaseModel

from clubs.validator import validate_club

TASK_STAGES = ("backlog", "active", "review", "blocked", "done")


class StatusError(RuntimeError):
    """Raised when status cannot be collected because the club is invalid."""


class AgentStatus(BaseModel):
    agent_id: str
    role: str
    state: str = "offline"
    current_task_id: str | None = None


class TaskCounts(BaseModel):
    backlog: int = 0
    active: int = 0
    review: int = 0
    blocked: int = 0
    done: int = 0


class ClubStatus(BaseModel):
    club_name: str
    workflow_pattern: str
    agents: list[AgentStatus]
    tasks: TaskCounts
    missions: int


def _agent_status(root: Path, agent_id: str, role: str) -> AgentStatus:
    state_file = root / ".clubs/runtime/state" / f"{agent_id}.json"
    if not state_file.is_file():
        return AgentStatus(agent_id=agent_id, role=role)
    try:
        payload = json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return AgentStatus(agent_id=agent_id, role=role)
    return AgentStatus(
        agent_id=agent_id, role=role,
        state=payload.get("status", "offline"),
        current_task_id=payload.get("current_task_id"),
    )


def _task_counts(root: Path) -> TaskCounts:
    counts = {stage: len(list((root / "tasks" / stage).glob("*.json"))) for stage in TASK_STAGES}
    return TaskCounts(**counts)


def collect_status(root: Path) -> ClubStatus:
    """Build a status snapshot, raising StatusError if the club fails validation."""
    result = validate_club(root)
    if not result.ok:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in result.issues)
        raise StatusError(f"Club configuration is invalid. Run 'clubs validate' for details. {details}")

    config_raw = yaml.safe_load((root / ".clubs/club.yaml").read_text(encoding="utf-8"))
    agents = [_agent_status(root, agent_id, data["role"]) for agent_id, data in config_raw["agents"].items()]
    missions = len(list((root / ".clubs/missions").glob("*.json")))
    return ClubStatus(
        club_name=config_raw["club"]["name"],
        workflow_pattern=config_raw["workflow"]["pattern"],
        agents=agents,
        tasks=_task_counts(root),
        missions=missions,
    )
