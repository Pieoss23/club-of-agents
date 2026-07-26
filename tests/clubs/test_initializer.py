from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from clubs.initializer import InitializationError, initialize_club, normalize_relative_path
from clubs.models import DEFAULT_ROLE_IDS, DEFAULT_WORKFLOW

from conftest import make_init_answers as answers


def test_initialization_creates_required_files_and_default_configuration(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    required = (
        ".clubs/club.yaml", "MASTER_CONTRACT.md", "docs/product/PRODUCT_OVERVIEW.md",
        "docs/architecture/SYSTEM_ARCHITECTURE.md", "docs/delivery/AGENT_OPERATING_MODEL.md",
        "docs/features/FEATURE_TEMPLATE.md", "docs/decisions/ADR_TEMPLATE.md",
        "docs/handoffs/HANDOFF_TEMPLATE.md", "tasks/backlog", "tasks/active", "tasks/review",
        "tasks/blocked", "tasks/done", "logs/audit", "logs/tests", "logs/agents",
        ".clubs/runtime/inbox", ".clubs/runtime/outbox", ".clubs/runtime/state",
        ".clubs/runtime/locks", ".clubs/runtime/events", ".clubs/missions",
    )
    for relative_path in required:
        assert (tmp_path / relative_path).exists(), relative_path

    config = yaml.safe_load((tmp_path / ".clubs/club.yaml").read_text(encoding="utf-8"))
    assert config["workflow"]["pattern"] == DEFAULT_WORKFLOW
    assert tuple(config["agents"]) == DEFAULT_ROLE_IDS
    assert config["agents"]["planner"]["can_plan"] is True
    assert config["agents"]["developer"]["can_code"] is True
    assert config["agents"]["reviewer"]["can_review"] is True
    assert config["agents"]["coordinator"]["can_merge"] is True


def test_custom_master_contract_path_is_normalized_and_generated(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path, master_contract=r"docs\governance\CONTRACT.md"))
    assert (tmp_path / "docs/governance/CONTRACT.md").is_file()
    assert not (tmp_path / "MASTER_CONTRACT.md").exists()
    config = yaml.safe_load((tmp_path / ".clubs/club.yaml").read_text(encoding="utf-8"))
    assert config["repository"]["master_contract"] == "docs/governance/CONTRACT.md"


def test_repeated_initialization_never_overwrites_without_force(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    contract = tmp_path / "MASTER_CONTRACT.md"
    contract.write_text("keep this", encoding="utf-8")
    with pytest.raises(InitializationError, match="would overwrite"):
        initialize_club(answers(tmp_path))
    assert contract.read_text(encoding="utf-8") == "keep this"


def test_force_is_explicit_and_replaces_generated_file(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    contract = tmp_path / "MASTER_CONTRACT.md"
    contract.write_text("replace me", encoding="utf-8")
    initialize_club(answers(tmp_path), force=True)
    assert "Master Contract" in contract.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("provided", "expected"),
    [(r"docs\product\MASTER_CONTRACT.md", "docs/product/MASTER_CONTRACT.md"),
     ("docs/product/MASTER_CONTRACT.md", "docs/product/MASTER_CONTRACT.md")],
)
def test_windows_and_unix_relative_paths_are_supported(provided: str, expected: str) -> None:
    assert normalize_relative_path(provided) == expected
