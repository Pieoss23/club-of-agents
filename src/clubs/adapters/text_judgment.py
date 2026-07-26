"""Shared plan/review/configure for every provider that can only produce text --
no file-editing agency (Ollama/OpenAI/OpenRouter/Gemini, unlike Claude Code/Codex CLI
which are full agentic coding tools). Every subclass supplies one method,
`_complete(prompt) -> str`; this mixin builds plan/review/configure on top of it,
and implement() always raises since none of these can actually edit files.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from clubs import git_ops, patterns, runtime, tasks, workflow
from clubs.adapters.audit_log import write_log
from clubs.adapters.errors import ProviderError
from clubs.adapters.mechanical import pending_missions
from clubs.adapters.prompts import (
    configure_prompt, parse_json_response, plan_prompt, read_master_contract, review_prompt,
)
from clubs.messaging import emit_event
from clubs.models import AgentConfig


class TextJudgmentMixin:
    """plan/review/configure built on self._complete(prompt) -> str."""

    def _complete(self, prompt: str) -> str:
        raise NotImplementedError

    def plan(self, root: Path, agent_id: str) -> None:
        pending = pending_missions(root)
        if not pending:
            return
        path, mission = pending[0]
        prompt = plan_prompt(read_master_contract(root), mission)
        reply = self._complete(prompt)
        write_log(root, agent_id, mission["id"], "plan", prompt=prompt, stdout=reply, stderr="")
        try:
            parsed = parse_json_response(reply)
            title, objective = parsed["title"], parsed["objective"]
        except (KeyError, ValueError) as error:
            raise ProviderError(f"could not parse plan response: {error}") from error
        workflow.decompose_mission(root, agent_id, path, mission, title=title, objective=objective)

    def implement(self, root: Path, agent_id: str) -> None:
        raise ProviderError(
            f"{type(self).__name__} cannot implement() -- it has no file-editing agency. "
            "Use shell/claude/codex for this agent's can_code capability."
        )

    def review(self, root: Path, agent_id: str) -> None:
        task = tasks.find_task(root, "review")
        if task is None or task.get("review_approved"):
            return
        worktree = workflow.real_worktree(root, task)
        if worktree is None:
            raise ProviderError(f"task {task['id']} has no isolated worktree; cannot compute a diff to review")
        diff = git_ops.diff_text(worktree, runtime.load_main_branch(root))
        prompt = review_prompt(read_master_contract(root), task, diff)
        reply = self._complete(prompt)
        write_log(root, agent_id, task["id"], "review", prompt=prompt, stdout=reply, stderr="")
        try:
            verdict = parse_json_response(reply)
        except ValueError as error:
            raise ProviderError(f"could not parse review response: {error}") from error

        if verdict.get("approved"):
            for criterion in task["acceptance_criteria"]:
                criterion["verified"] = True
                criterion["evidence"] = f"{type(self).__name__} review: approved"
            task.setdefault("notes", []).append(f"Reviewed and approved by {type(self).__name__}.")
            workflow.approve_review(root, agent_id, task)
        else:
            workflow.reject_review(root, agent_id, task, verdict.get("findings", []))

    def configure(self, root: Path, agent_id: str) -> None:
        """Bootstrap the club's roster from the first pending mission's description,
        once. Never assigns real providers to the roles it creates -- every new role
        defaults to 'dummy'; switching one to a real, costly provider stays a
        separate, explicit human edit to club.yaml."""
        club_yaml_path = root / ".clubs/club.yaml"
        raw = yaml.safe_load(club_yaml_path.read_text(encoding="utf-8"))
        if raw["club"].get("bootstrapped"):
            return

        pending = pending_missions(root)
        if not pending:
            return
        _, mission = pending[0]

        prompt = configure_prompt(read_master_contract(root), mission, list(patterns.CAPABILITY_FIELDS))
        reply = self._complete(prompt)
        write_log(root, agent_id, mission["id"], "configure", prompt=prompt, stdout=reply, stderr="")
        try:
            parsed = parse_json_response(reply)
            role_capabilities = tuple(
                (role["id"], tuple(role["capabilities"])) for role in parsed["roles"]
            )
            new_agents = patterns.custom(role_capabilities)
        except (KeyError, ValueError) as error:
            raise ProviderError(f"could not parse configure response: {error}") from error

        # The running process's own agent id must survive, or its very next tick
        # raises UnknownAgentError once this rewrite takes effect.
        new_agents.setdefault(agent_id, AgentConfig(role=agent_id))

        raw["agents"] = {role_id: config.model_dump() for role_id, config in new_agents.items()}
        raw["club"]["bootstrapped"] = True
        club_yaml_path.write_text(yaml.safe_dump(raw, sort_keys=False, allow_unicode=True), encoding="utf-8")
        emit_event(root, "club.bootstrapped", agent_id=agent_id, roles=list(new_agents), mission_id=mission["id"])
