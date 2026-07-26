"""OpenAI Codex CLI headless adapter.

CLI contract confirmed via research this session: `codex exec "<prompt>" --sandbox <mode>`
runs one-shot; progress streams to stderr and only the final agent message is printed
to stdout. `--sandbox read-only` (default, used for plan/review) vs
`--sandbox workspace-write` (used for implement -- an OS-level write sandbox scoped to
the given cwd, which is a real safety property beyond tool-gating). Working directory
is set purely via the subprocess cwd.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from clubs import git_ops, runtime, tasks, workflow
from clubs.adapters.audit_log import write_log
from clubs.adapters.errors import ProviderError
from clubs.adapters.mechanical import MechanicalAssignMergeMixin, pending_missions
from clubs.adapters.prompts import implement_prompt, parse_json_response, plan_prompt, read_master_contract, review_prompt


@dataclass(frozen=True)
class CodexProvider(MechanicalAssignMergeMixin):
    timeout: int = 600
    run: Callable[..., subprocess.CompletedProcess] = field(default=subprocess.run)

    def _invoke(self, cwd: Path, prompt: str, *, allow_edits: bool) -> str:
        sandbox = "workspace-write" if allow_edits else "read-only"
        args = ["codex", "exec", prompt, "--sandbox", sandbox]
        try:
            result = self.run(args, cwd=cwd, capture_output=True, text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired as error:
            raise ProviderError(f"codex timed out after {self.timeout}s") from error
        except FileNotFoundError as error:
            raise ProviderError("codex CLI not found on PATH") from error
        if result.returncode != 0:
            raise ProviderError(f"codex CLI failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def plan(self, root: Path, agent_id: str) -> None:
        pending = pending_missions(root)
        if not pending:
            return
        path, mission = pending[0]
        prompt = plan_prompt(read_master_contract(root), mission)
        reply = self._invoke(root, prompt, allow_edits=False)
        write_log(root, agent_id, mission["id"], "plan", prompt=prompt, stdout=reply, stderr="")
        try:
            parsed = parse_json_response(reply)
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
            raise ProviderError(f"task {task['id']} has no isolated worktree; refusing to let codex edit the shared repo")
        prompt = implement_prompt(read_master_contract(root), task)
        reply = self._invoke(worktree, prompt, allow_edits=True)
        write_log(root, agent_id, task["id"], "implement", prompt=prompt, stdout=reply, stderr="")
        task.setdefault("notes", []).append(f"codex: {reply[:500]}")
        workflow.submit_for_review(root, agent_id, task)

    def review(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "review")
        if task is None or task.get("review_approved"):
            return
        worktree = workflow.real_worktree(root, task)
        if worktree is None:
            raise ProviderError(f"task {task['id']} has no isolated worktree; cannot compute a diff to review")
        diff = git_ops.diff_text(worktree, runtime.load_main_branch(root))
        prompt = review_prompt(read_master_contract(root), task, diff)
        reply = self._invoke(worktree, prompt, allow_edits=False)
        write_log(root, agent_id, task["id"], "review", prompt=prompt, stdout=reply, stderr="")
        try:
            verdict = parse_json_response(reply)
        except ValueError as error:
            raise ProviderError(f"could not parse review response: {error}") from error

        if verdict.get("approved"):
            for criterion in task["acceptance_criteria"]:
                criterion["verified"] = True
                criterion["evidence"] = "codex review: approved"
            task.setdefault("notes", []).append("Reviewed and approved by codex.")
            workflow.approve_review(root, agent_id, task)
        else:
            workflow.reject_review(root, agent_id, task, verdict.get("findings", []))
