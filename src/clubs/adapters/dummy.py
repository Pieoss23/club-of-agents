"""Mechanical, non-AI provider: proves the orchestration mechanics, writes no real code.

Real code generation is a later milestone (provider adapters, master prompt SS10).
This provider only supplies judgment (what to create, whether to approve) --
the mechanics of every stage transition live in clubs.workflow.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from clubs import tasks, workflow
from clubs.models import AgentConfig


def _pending_missions(root: Path) -> list[tuple[Path, dict]]:
    missions_dir = root / ".clubs/missions"
    if not missions_dir.is_dir():
        return []
    pending = []
    for path in sorted(missions_dir.glob("MISSION-*.json")):
        mission = json.loads(path.read_text(encoding="utf-8"))
        if mission.get("status") == "planning" and not mission.get("tasks"):
            pending.append((path, mission))
    return pending


class DummyProvider:
    """Reference provider used before a real Codex/Claude adapter exists.

    `work_seconds` simulates implementation latency, purely so a live demo across
    multiple terminals is watchable. Tests should leave it at 0 (the default).
    """

    def __init__(self, work_seconds: float = 0.0) -> None:
        self.work_seconds = work_seconds

    def plan(self, root: Path, agent_id: str) -> None:
        pending = _pending_missions(root)
        if not pending:
            return
        path, mission = pending[0]
        workflow.decompose_mission(root, agent_id, path, mission, title=mission["title"], objective=mission["description"])

    def assign(self, root: Path, agent_id: str, agents: dict[str, AgentConfig]) -> None:
        task = tasks.find_task(root, "backlog")
        if task is None:
            return
        assignee_id = workflow.eligible_assignee(root, agents)
        if assignee_id is None:
            return
        workflow.assign_task(root, agent_id, task, assignee_id, agents[assignee_id].role)

    def implement(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "active", owner=agent_id)
        if task is None:
            return
        if self.work_seconds:
            time.sleep(self.work_seconds)
        for criterion in task["acceptance_criteria"]:
            criterion["verified"] = True
            criterion["evidence"] = "dummy provider"
        task.setdefault("notes", []).append(f"Implemented by dummy provider ({agent_id}).")
        workflow.submit_for_review(root, agent_id, task)

    def review(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "review")
        if task is None or task.get("review_approved"):
            return
        task.setdefault("notes", []).append(f"Reviewed and approved by dummy provider ({agent_id}).")
        workflow.approve_review(root, agent_id, task)

    def merge(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "review")
        if task is None or not task.get("review_approved"):
            return
        workflow.integrate(root, agent_id, task)
