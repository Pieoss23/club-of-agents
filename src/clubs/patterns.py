"""Role/capability builders for each supported collaboration pattern."""

from __future__ import annotations

from clubs.models import AgentConfig

PLANNER_DEVELOPER_REVIEWER_COORDINATOR = "planner-developer-reviewer-coordinator"
MASTER_WORKERS = "master-workers"
ARCHITECT_FRONTEND_BACKEND_REVIEWER = "architect-frontend-backend-reviewer"
SWARM_BY_COMPONENT = "swarm-by-component"
CUSTOM = "custom"

PATTERN_IDS = (
    PLANNER_DEVELOPER_REVIEWER_COORDINATOR,
    MASTER_WORKERS,
    ARCHITECT_FRONTEND_BACKEND_REVIEWER,
    SWARM_BY_COMPONENT,
    CUSTOM,
)

PATTERN_LABELS = {
    PLANNER_DEVELOPER_REVIEWER_COORDINATOR: "Planner -> Developer -> Reviewer -> Coordinator",
    MASTER_WORKERS: "Master -> Workers",
    ARCHITECT_FRONTEND_BACKEND_REVIEWER: "Architect -> Frontend -> Backend -> Reviewer",
    SWARM_BY_COMPONENT: "Swarm by component",
    CUSTOM: "Custom",
}

CAPABILITY_FIELDS = {
    "plan": "can_plan",
    "code": "can_code",
    "review": "can_review",
    "assign": "can_assign",
    "merge": "can_merge",
}

_DEFAULT_CAPABILITIES = {
    "planner": {"can_plan": True},
    "developer": {"can_code": True},
    "reviewer": {"can_review": True},
    "coordinator": {"can_assign": True, "can_merge": True},
}


def planner_developer_reviewer_coordinator(role_ids: tuple[str, ...]) -> dict[str, AgentConfig]:
    """Default pattern: capabilities inferred by canonical role name, unknown names get none."""
    agents: dict[str, AgentConfig] = {}
    for role_id in role_ids:
        agents[role_id] = AgentConfig(role=role_id, **_DEFAULT_CAPABILITIES.get(role_id, {}))
    return agents


def master_workers(worker_count: int) -> dict[str, AgentConfig]:
    """One master that plans/assigns/merges, N workers that implement."""
    if worker_count < 1:
        raise ValueError("At least one worker is required.")
    agents: dict[str, AgentConfig] = {
        "master": AgentConfig(role="master", can_plan=True, can_assign=True, can_merge=True),
    }
    for index in range(1, worker_count + 1):
        role_id = f"worker-{index}"
        agents[role_id] = AgentConfig(role=role_id, can_code=True)
    return agents


def architect_frontend_backend_reviewer() -> dict[str, AgentConfig]:
    """Fixed four-role pattern for a typical full-stack feature team."""
    return {
        "architect": AgentConfig(role="architect", can_plan=True),
        "frontend": AgentConfig(role="frontend", can_code=True),
        "backend": AgentConfig(role="backend", can_code=True),
        "reviewer": AgentConfig(role="reviewer", can_review=True),
    }


def swarm_by_component(components: tuple[str, ...]) -> dict[str, AgentConfig]:
    """One implementing agent per component, no hierarchy."""
    if not components:
        raise ValueError("At least one component is required.")
    return {component: AgentConfig(role=component, can_code=True) for component in components}


def custom(role_capabilities: tuple[tuple[str, tuple[str, ...]], ...]) -> dict[str, AgentConfig]:
    """User-defined roles with explicitly chosen capabilities."""
    if not role_capabilities:
        raise ValueError("At least one role is required.")
    agents: dict[str, AgentConfig] = {}
    for role_id, selected in role_capabilities:
        unknown = [label for label in selected if label not in CAPABILITY_FIELDS]
        if unknown:
            raise ValueError(f"Unknown capability label(s): {', '.join(unknown)}")
        kwargs = {CAPABILITY_FIELDS[label]: True for label in selected}
        agents[role_id] = AgentConfig(role=role_id, **kwargs)
    return agents
