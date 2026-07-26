from __future__ import annotations

import pytest

from clubs import patterns


def test_planner_developer_reviewer_coordinator_assigns_known_capabilities() -> None:
    agents = patterns.planner_developer_reviewer_coordinator(("planner", "developer", "reviewer", "coordinator"))
    assert agents["planner"].can_plan is True
    assert agents["developer"].can_code is True
    assert agents["reviewer"].can_review is True
    assert agents["coordinator"].can_assign is True
    assert agents["coordinator"].can_merge is True


def test_planner_developer_reviewer_coordinator_unknown_name_gets_no_capabilities() -> None:
    agents = patterns.planner_developer_reviewer_coordinator(("planner", "extra"))
    assert agents["extra"].model_dump(exclude={
        "role", "shell", "provider", "provider_command", "provider_model", "provider_base_url", "can_bootstrap",
    }) == {
        "can_plan": False, "can_code": False, "can_review": False, "can_assign": False, "can_merge": False,
    }


def test_master_workers_creates_master_and_numbered_workers() -> None:
    agents = patterns.master_workers(3)
    assert set(agents) == {"master", "worker-1", "worker-2", "worker-3"}
    assert agents["master"].can_plan is True
    assert agents["master"].can_assign is True
    assert agents["master"].can_merge is True
    assert agents["worker-1"].can_code is True
    assert agents["worker-1"].can_plan is False


def test_master_workers_requires_at_least_one_worker() -> None:
    with pytest.raises(ValueError):
        patterns.master_workers(0)


def test_architect_frontend_backend_reviewer_has_fixed_roles() -> None:
    agents = patterns.architect_frontend_backend_reviewer()
    assert set(agents) == {"architect", "frontend", "backend", "reviewer"}
    assert agents["architect"].can_plan is True
    assert agents["frontend"].can_code is True
    assert agents["backend"].can_code is True
    assert agents["reviewer"].can_review is True


def test_swarm_by_component_grants_can_code_to_every_component() -> None:
    agents = patterns.swarm_by_component(("auth", "billing"))
    assert set(agents) == {"auth", "billing"}
    assert all(agent.can_code for agent in agents.values())
    assert all(not agent.can_plan and not agent.can_assign for agent in agents.values())


def test_swarm_by_component_requires_at_least_one_component() -> None:
    with pytest.raises(ValueError):
        patterns.swarm_by_component(())


def test_custom_maps_capability_labels_to_agent_config() -> None:
    agents = patterns.custom((("lead", ("plan", "assign", "merge")), ("builder", ("code",))))
    assert agents["lead"].can_plan is True
    assert agents["lead"].can_assign is True
    assert agents["lead"].can_merge is True
    assert agents["builder"].can_code is True
    assert agents["builder"].can_plan is False


def test_custom_rejects_unknown_capability_label() -> None:
    with pytest.raises(ValueError):
        patterns.custom((("lead", ("fly",)),))


def test_custom_requires_at_least_one_role() -> None:
    with pytest.raises(ValueError):
        patterns.custom(())
