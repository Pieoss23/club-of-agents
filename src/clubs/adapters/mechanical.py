"""Provider capabilities that are pure role/state matching -- no judgment involved,
shared by every provider (dummy and real) instead of each reimplementing them.
"""

from __future__ import annotations

import json
from pathlib import Path

from clubs import tasks, workflow
from clubs.models import AgentConfig


def pending_missions(root: Path) -> list[tuple[Path, dict]]:
    """Missions still in 'planning' with no task decomposed from them yet."""
    missions_dir = root / ".clubs/missions"
    if not missions_dir.is_dir():
        return []
    pending = []
    for path in sorted(missions_dir.glob("MISSION-*.json")):
        mission = json.loads(path.read_text(encoding="utf-8"))
        if mission.get("status") == "planning" and not mission.get("tasks"):
            pending.append((path, mission))
    return pending


class MechanicalAssignMergeMixin:
    """assign(): match a backlog task to the first free, capable agent.
    merge(): move an approved review task to done.
    Neither requires real judgment, so every provider shares this unchanged."""

    def assign(self, root: Path, agent_id: str, agents: dict[str, AgentConfig]) -> None:
        task = tasks.find_task(root, "backlog")
        if task is None:
            return
        assignee_id = workflow.eligible_assignee(root, agents)
        if assignee_id is None:
            return
        workflow.assign_task(root, agent_id, task, assignee_id, agents[assignee_id].role)

    def merge(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "review")
        if task is None or not task.get("review_approved"):
            return
        workflow.integrate(root, agent_id, task)
