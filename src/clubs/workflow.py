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

from clubs import git_ops, path_policy, runtime, tasks
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

    try:
        info = git_ops.create_worktree(
            root, role=assignee_role, task_id=task["id"], task_title=task["title"],
            base_branch=runtime.load_main_branch(root),
        )
    except git_ops.GitError as error:
        emit_event(root, "worktree.unavailable", task_id=task["id"], reason=str(error))
    else:
        task["owner"]["branch"] = info.branch
        task["owner"]["worktree"] = str(info.path)
        emit_event(root, "worktree.created", task_id=task["id"], branch=info.branch, path=str(info.path))

    tasks.save_task(moved, task)
    runtime.write_state(root, assignee_id, status="assigned", current_task_id=task["id"])
    send_message(root, from_agent=agent_id, to_agent=assignee_id, type="task.assigned", task_id=task["id"])
    emit_event(root, "task.assigned", task_id=task["id"], owner=assignee_id, by=agent_id)
    return moved


def real_worktree(root: Path, task: dict) -> Path | None:
    """The task's owner.worktree, if isolation actually created a real sibling worktree
    (not the same-directory placeholder used when git isolation wasn't available)."""
    worktree = (task.get("owner") or {}).get("worktree")
    if not worktree:
        return None
    path = Path(worktree)
    if path == root:
        return None
    return path if path.is_dir() else None


def submit_for_review(root: Path, agent_id: str, task: dict) -> Path | None:
    """Move an implemented task to review, then save its updated content.
    Returns None if another process claimed it first."""
    worktree_path = real_worktree(root, task)
    if worktree_path is not None:
        sha = git_ops.commit_all(worktree_path, f"{task['id']}: {task['title']}")
        if sha is not None:
            task["audit"]["commits"].append(sha)
        base_branch = runtime.load_main_branch(root)
        changed = git_ops.changed_paths(worktree_path, base_branch)
        violations = path_policy.check(changed, task["allowed_paths"], task["forbidden_paths"])
        if violations:
            task.setdefault("notes", []).extend(violations)
            for violation in violations:
                emit_event(root, "path_policy.violation", task_id=task["id"], violation=violation)

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


def reject_review(root: Path, agent_id: str, task: dict, findings: list[str] | None = None) -> Path | None:
    """Send a rejected task back to active for its original owner to rework.
    Returns None if another process already moved it out of review."""
    task["review_approved"] = False
    if findings:
        task.setdefault("notes", []).extend(f"Review finding: {finding}" for finding in findings)
    else:
        task.setdefault("notes", []).append("Review rejected: changes requested.")

    moved = tasks.move_task(root, task["id"], from_stage="review", to_stage="active")
    if moved is None:
        return None
    tasks.save_task(moved, task)

    owner_id = (task.get("owner") or {}).get("agent_id")
    if owner_id:
        # Without this, eligible_assignee (see above) would see the owner's stale "idle"
        # state -- only refreshed at the end of *their own* tick -- and let the
        # coordinator double-book them with a new backlog task before their next tick
        # naturally re-picks-up this one via find_task("active", owner=owner_id).
        runtime.write_state(root, owner_id, status="assigned", current_task_id=task["id"])
        send_message(root, from_agent=agent_id, to_agent=owner_id, type="review.rejected", task_id=task["id"])
    emit_event(root, "review.rejected", task_id=task["id"], by=agent_id)
    return moved


def _write_pull_request_draft(root: Path, task: dict) -> str:
    """Write a local PR title/body draft (no network calls, nothing pushed) and return
    its repository-relative path for task['audit']['pull_request']."""
    branch = task["owner"]["branch"]
    base_branch = runtime.load_main_branch(root)
    checklist = "\n".join(
        f"- [{'x' if criterion['verified'] else ' '}] {criterion['description']}"
        for criterion in task["acceptance_criteria"]
    )
    body = (
        f"## Objective\n{task['objective']}\n\n"
        f"## Acceptance criteria\n{checklist}\n\n"
        f"Branch: `{branch}` -> `{base_branch}`\n"
    )
    relative_path = f"docs/handoffs/{task['id']}-pr-draft.md"
    draft_path = root / relative_path
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(f"# {task['id']}: {task['title']}\n\n{body}", encoding="utf-8")
    return relative_path


def integrate(root: Path, agent_id: str, task: dict) -> Path | None:
    """Move an approved task to done, then close it out. Returns None if another process claimed it first."""
    if real_worktree(root, task) is not None:
        task["audit"]["pull_request"] = _write_pull_request_draft(root, task)

    moved = tasks.move_task(root, task["id"], from_stage="review", to_stage="done")
    if moved is None:
        return None
    task["status"] = "done"
    task["audit"]["completed_at"] = tasks.now_iso()
    tasks.save_task(moved, task)
    emit_event(root, "task.completed", task_id=task["id"], by=agent_id)
    return moved
