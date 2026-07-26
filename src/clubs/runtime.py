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


def run_agent_tick(root: Path, agent_id: str, provider: Provider) -> AgentState:
    """Run one poll cycle for a single agent and return its resulting state."""
    agents = load_agents(root)
    if agent_id not in agents:
        raise UnknownAgentError(f"'{agent_id}' is not a configured agent in this club.")
    config = agents[agent_id]

    write_state(root, agent_id, status="working", last_heartbeat=now_iso())
    messaging.route_messages(root)

    if config.can_plan:
        provider.plan(root, agent_id)
    if config.can_assign:
        provider.assign(root, agent_id, agents)
    if config.can_code:
        provider.implement(root, agent_id)
    if config.can_review:
        provider.review(root, agent_id)
    if config.can_merge:
        provider.merge(root, agent_id)

    messaging.route_messages(root)
    current_task = tasks.find_task(root, "active", owner=agent_id)
    return write_state(
        root, agent_id, status="idle",
        current_task_id=current_task["id"] if current_task else None,
    )
