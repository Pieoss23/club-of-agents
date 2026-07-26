"""Fully generic provider: shells out to a user-supplied command with the task/mission
context as JSON on stdin. Lets someone plug in anything -- a wrapper script, a
different LLM CLI, a human-in-the-loop notifier -- without this project knowing or
caring what's on the other end (core principle: the core stays provider-agnostic).

Contract: the command receives {"capability", "agent_id", "root", "worktree", ...}
as JSON on stdin, does its work, and prints its result to stdout. plan/review must
print a single JSON object (see adapters.prompts.parse_json_response); implement
just prints free text (recorded as a task note).
"""

from __future__ import annotations

import json
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from clubs import git_ops, runtime, tasks, workflow
from clubs.adapters.audit_log import write_log
from clubs.adapters.errors import ProviderError
from clubs.adapters.mechanical import MechanicalAssignMergeMixin, pending_missions
from clubs.adapters.prompts import parse_json_response


@dataclass(frozen=True)
class ShellProvider(MechanicalAssignMergeMixin):
    command: str
    timeout: int = 600
    run: Callable[..., subprocess.CompletedProcess] = field(default=subprocess.run)

    def _invoke(self, cwd: Path, payload: dict) -> subprocess.CompletedProcess:
        try:
            result = self.run(
                shlex.split(self.command), input=json.dumps(payload), cwd=cwd,
                capture_output=True, text=True, timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise ProviderError(f"shell provider timed out after {self.timeout}s") from error
        except FileNotFoundError as error:
            raise ProviderError(f"shell command not found: {self.command}") from error
        if result.returncode != 0:
            raise ProviderError(f"shell provider failed: {result.stderr.strip()}")
        return result

    def plan(self, root: Path, agent_id: str) -> None:
        pending = pending_missions(root)
        if not pending:
            return
        path, mission = pending[0]
        payload = {"capability": "plan", "agent_id": agent_id, "root": str(root), "mission": mission}
        result = self._invoke(root, payload)
        write_log(root, agent_id, mission["id"], "plan", prompt=json.dumps(payload), stdout=result.stdout, stderr=result.stderr)
        try:
            parsed = parse_json_response(result.stdout)
            title, objective = parsed["title"], parsed["objective"]
        except (KeyError, ValueError) as error:
            raise ProviderError(f"could not parse plan response: {error}") from error
        workflow.decompose_mission(root, agent_id, path, mission, title=title, objective=objective)

    def implement(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "active", owner=agent_id)
        if task is None:
            return
        worktree = workflow.real_worktree(root, task)
        if worktree is None:
            raise ProviderError(f"task {task['id']} has no isolated worktree; refusing to run the shell provider against the shared repo")
        payload = {"capability": "implement", "agent_id": agent_id, "root": str(root), "worktree": str(worktree), "task": task}
        result = self._invoke(worktree, payload)
        write_log(root, agent_id, task["id"], "implement", prompt=json.dumps(payload), stdout=result.stdout, stderr=result.stderr)
        task.setdefault("notes", []).append(f"shell provider: {result.stdout.strip()[:500]}")
        workflow.submit_for_review(root, agent_id, task)

    def review(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "review")
        if task is None or task.get("review_approved"):
            return
        worktree = workflow.real_worktree(root, task)
        if worktree is None:
            raise ProviderError(f"task {task['id']} has no isolated worktree; cannot compute a diff to review")
        diff = git_ops.diff_text(worktree, runtime.load_main_branch(root))
        payload = {"capability": "review", "agent_id": agent_id, "root": str(root), "worktree": str(worktree), "task": task, "diff": diff}
        result = self._invoke(worktree, payload)
        write_log(root, agent_id, task["id"], "review", prompt=json.dumps(payload), stdout=result.stdout, stderr=result.stderr)
        try:
            verdict = parse_json_response(result.stdout)
        except ValueError as error:
            raise ProviderError(f"could not parse review response: {error}") from error

        if verdict.get("approved"):
            for criterion in task["acceptance_criteria"]:
                criterion["verified"] = True
                criterion["evidence"] = "shell provider review: approved"
            task.setdefault("notes", []).append("Reviewed and approved by shell provider.")
            workflow.approve_review(root, agent_id, task)
        else:
            workflow.reject_review(root, agent_id, task, verdict.get("findings", []))
