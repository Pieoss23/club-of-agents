"""Provider adapter interface: capability-shaped hooks called by the agent runner."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from clubs.models import AgentConfig


class Provider(Protocol):
    """One method per agent capability. A runner calls only the methods matching
    the agent's granted capabilities (can_plan, can_assign, can_code, can_review, can_merge)."""

    def plan(self, root: Path, agent_id: str) -> None: ...

    def assign(self, root: Path, agent_id: str, agents: dict[str, AgentConfig]) -> None: ...

    def implement(self, root: Path, agent_id: str) -> None: ...

    def review(self, root: Path, agent_id: str) -> None: ...

    def merge(self, root: Path, agent_id: str) -> None: ...
