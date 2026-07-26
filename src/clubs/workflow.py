"""Provider-independent stage-transition mechanics.

Every one of these functions is the mechanical half of a workflow step: it moves
task JSON between stage directories, writes state, sends messages, and emits
events. None of them decide *whether* a transition should happen or *what*
content it should carry -- that judgment stays in the calling provider
(e.g. adapters/dummy.py). This split means a future real provider (Claude/Codex,
still out of scope) reuses all of this instead of reimplementing it.
"""

from __future__ import annotations

import json
from pathlib import Path

from clubs import runtime, tasks
from clubs.messaging import emit_event, send_message
from clubs.models import AgentConfig


def eligible_assignee(root: Path, agents: dict[str, AgentConfig], *, capability: str = "can_code") -> str | None:
    """First configured agent with the given capability that isn't already holding a task."""
    return next(
        (
            candidate_id for candidate_id, config in agents.items()
            if getattr(config, capability, False) and runtime.read_state(root, candidate_id).current_task_id is None
        ),
        None,
    )


def decompose_mission(root: Path, agent_id: str, mission_path: Path, mission: dict, *, title: str, objective: str) -> dict:
    """Create one task from a pending mission and mark the mission active."""
    task = tasks.create_task(root, mission_id=mission["id"], title=title, objective=objective)
    mission["status"] = "active"
    mission["tasks"] = [task["id"]]
    mission_path.write_text(json.dumps(mission, indent=2) + "\n", encoding="utf-8")
    send_message(root, from_agent=agent_id, to_agent="coordinator", type="task.created", task_id=task["id"])
    emit_event(root, "task.created", task_id=task["id"], mission_id=mission["id"], by=agent_id)
    return task


def assign_task(root: Path, agent_id: str, task: dict, assignee_id: str, assignee_role: str) -> Path | None:
    """Move a backlog task to active, then record the assignment. Returns None if
    another process claimed it first -- the rename happens *before* any mutation
    is written, so a lost race never resurrects a file at the old path."""
    moved = tasks.move_task(root, task["id"], from_stage="backlog", to_stage="active")
    if moved is None:
        return None
    task["owner"] = {
        "agent_id": assignee_id, "role": assignee_role,
        "branch": "unavailable-not-a-git-worktree", "worktree": str(root),
    }
    task["audit"]["started_at"] = tasks.now_iso()
    tasks.save_task(moved, task)
    runtime.write_state(root, assignee_id, status="assigned", current_task_id=task["id"])
    send_message(root, from_agent=agent_id, to_agent=assignee_id, type="task.assigned", task_id=task["id"])
    emit_event(root, "task.assigned", task_id=task["id"], owner=assignee_id, by=agent_id)
    return moved


def submit_for_review(root: Path, agent_id: str, task: dict) -> Path | None:
    """Move an implemented task to review, then save its updated content.
    Returns None if another process claimed it first."""
    moved = tasks.move_task(root, task["id"], from_stage="active", to_stage="review")
    if moved is None:
        return None
    tasks.save_task(moved, task)
    send_message(root, from_agent=agent_id, to_agent="reviewer", type="task.ready_for_review", task_id=task["id"])
    emit_event(root, "task.ready_for_review", task_id=task["id"], by=agent_id)
    return moved


def approve_review(root: Path, agent_id: str, task: dict) -> None:
    """Record review approval in place. Does not decide whether approval is warranted."""
    task["review_approved"] = True
    tasks.save_task(root / "tasks/review" / f"{task['id']}.json", task)
    send_message(root, from_agent=agent_id, to_agent="coordinator", type="review.approved", task_id=task["id"])
    emit_event(root, "review.approved", task_id=task["id"], by=agent_id)


def integrate(root: Path, agent_id: str, task: dict) -> Path | None:
    """Move an approved task to done, then close it out. Returns None if another process claimed it first."""
    moved = tasks.move_task(root, task["id"], from_stage="review", to_stage="done")
    if moved is None:
        return None
    task["status"] = "done"
    task["audit"]["completed_at"] = tasks.now_iso()
    tasks.save_task(moved, task)
    emit_event(root, "task.completed", task_id=task["id"], by=agent_id)
    return moved
