"""Mechanical, non-AI provider: proves the orchestration mechanics, writes no real code.

Real code generation is a later milestone (provider adapters, master prompt SS10).
This provider only supplies judgment (what to create, whether to approve) --
the mechanics of every stage transition live in clubs.workflow.
"""

from __future__ import annotations

import time
from pathlib import Path

from clubs import tasks, workflow
from clubs.adapters.mechanical import MechanicalAssignMergeMixin, pending_missions


class DummyProvider(MechanicalAssignMergeMixin):
    """Reference provider used before a real Codex/Claude adapter exists.

    `work_seconds` simulates implementation latency, purely so a live demo across
    multiple terminals is watchable. Tests should leave it at 0 (the default).
    """

    def __init__(self, work_seconds: float = 0.0) -> None:
        self.work_seconds = work_seconds

    def plan(self, root: Path, agent_id: str) -> None:
        pending = pending_missions(root)
        if not pending:
            return
        path, mission = pending[0]
        workflow.decompose_mission(root, agent_id, path, mission, title=mission["title"], objective=mission["description"])

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

        worktree = workflow.real_worktree(root, task)
        if worktree is not None:
            notes_path = worktree / "NOTES.md"
            existing = notes_path.read_text(encoding="utf-8") if notes_path.is_file() else ""
            notes_path.write_text(existing + f"{agent_id} implemented: {task['title']}\n", encoding="utf-8")

        workflow.submit_for_review(root, agent_id, task)

    def review(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "review")
        if task is None or task.get("review_approved"):
            return
        task.setdefault("notes", []).append(f"Reviewed and approved by dummy provider ({agent_id}).")
        workflow.approve_review(root, agent_id, task)
