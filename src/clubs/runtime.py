"""The per-agent poll cycle: heartbeat, message routing, and capability-driven work.

`run_agent_tick` is one full cycle and is fully unit-testable without sleeping.
The `while True: sleep(...)` wrapper lives only in the CLI command (cli.py).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel

from clubs import messaging, tasks
from clubs.adapters.base import Provider
from clubs.adapters.errors import ProviderError
from clubs.models import AgentConfig
from clubs.tasks import now_iso

AGENT_STATUSES = (
    "offline", "starting", "idle", "assigned", "working",
    "waiting", "blocked", "reviewing", "completed", "failed",
)
STATE_DIR = ".clubs/runtime/state"


class UnknownAgentError(RuntimeError):
    """Raised when the requested agent id isn't configured in this club."""


class AgentState(BaseModel):
    status: str = "offline"
    current_task_id: str | None = None
    last_heartbeat: str | None = None
    updated_at: str | None = None


def _state_path(root: Path, agent_id: str) -> Path:
    return root / STATE_DIR / f"{agent_id}.json"


def read_state(root: Path, agent_id: str) -> AgentState:
    path = _state_path(root, agent_id)
    if not path.is_file():
        return AgentState()
    try:
        return AgentState.model_validate_json(path.read_text(encoding="utf-8"))
    except ValueError:
        return AgentState()


def write_state(root: Path, agent_id: str, **fields: object) -> AgentState:
    updated = read_state(root, agent_id).model_copy(update=fields)
    updated.updated_at = now_iso()
    path = _state_path(root, agent_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(updated.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return updated


def load_agents(root: Path) -> dict[str, AgentConfig]:
    raw = yaml.safe_load((root / ".clubs/club.yaml").read_text(encoding="utf-8"))
    return {agent_id: AgentConfig(**data) for agent_id, data in raw["agents"].items()}


def load_polling_interval(root: Path) -> int:
    raw = yaml.safe_load((root / ".clubs/club.yaml").read_text(encoding="utf-8"))
    return raw["runtime"]["polling_interval_seconds"]


def load_main_branch(root: Path) -> str:
    raw = yaml.safe_load((root / ".clubs/club.yaml").read_text(encoding="utf-8"))
    return raw["repository"]["main_branch"]


def load_provider_timeout_seconds(root: Path) -> int:
    raw = yaml.safe_load((root / ".clubs/club.yaml").read_text(encoding="utf-8"))
    return raw.get("runtime", {}).get("provider_timeout_seconds", 600)


def _safe_call(root: Path, agent_id: str, capability: str, fn) -> None:
    """Run one provider capability; a ProviderError (real-provider subprocess failure,
    timeout, or unparsable output) is logged and swallowed so it never crashes the
    whole poll loop -- the agent just stays idle and retries next tick."""
    try:
        fn()
    except ProviderError as error:
        messaging.emit_event(root, "provider.failed", agent_id=agent_id, capability=capability, reason=str(error))


def run_agent_tick(root: Path, agent_id: str, provider: Provider) -> AgentState:
    """Run one poll cycle for a single agent and return its resulting state."""
    agents = load_agents(root)
    if agent_id not in agents:
        raise UnknownAgentError(f"'{agent_id}' is not a configured agent in this club.")
    config = agents[agent_id]

    write_state(root, agent_id, status="working", last_heartbeat=now_iso())
    messaging.route_messages(root)

    messaging.process_communication_messages(root, agent_id)

    if config.can_bootstrap:
        _safe_call(root, agent_id, "configure", lambda: provider.configure(root, agent_id))
        agents = load_agents(root)  # bootstrap may have just rewritten club.yaml
        if agent_id not in agents:
            raise UnknownAgentError(f"'{agent_id}' no longer exists in club.yaml after bootstrap.")
        config = agents[agent_id]

    if config.can_plan:
        _safe_call(root, agent_id, "plan", lambda: provider.plan(root, agent_id))
    if config.can_assign:
        _safe_call(root, agent_id, "assign", lambda: provider.assign(root, agent_id, agents))
    if config.can_code:
        _safe_call(root, agent_id, "implement", lambda: provider.implement(root, agent_id))
    if config.can_review:
        _safe_call(root, agent_id, "review", lambda: provider.review(root, agent_id))
    if config.can_merge:
        _safe_call(root, agent_id, "merge", lambda: provider.merge(root, agent_id))

    messaging.route_messages(root)
    current_task = tasks.find_task(root, "active", owner=agent_id)
    return write_state(
        root, agent_id, status="idle",
        current_task_id=current_task["id"] if current_task else None,
    )
