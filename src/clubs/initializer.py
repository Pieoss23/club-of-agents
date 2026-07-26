"""Filesystem-safe project initialization for Clubs of Agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
import re
from typing import Iterable

import yaml

from clubs import patterns
from clubs.models import (
    AgentConfig, ClubConfig, ClubDetails, DEFAULT_ROLE_IDS, DEFAULT_WORKFLOW,
    RepositoryConfig, WorkflowConfig,
)
from clubs.templates import DOCUMENT_TEMPLATES, render_template


class InitializationError(RuntimeError):
    """Raised when a requested club cannot safely be initialized."""


ROLE_NAME = re.compile(r"^[a-z][a-z0-9-]*$")

REQUIRED_DIRECTORIES = (
    "tasks/backlog", "tasks/active", "tasks/review", "tasks/blocked", "tasks/done",
    "logs/audit", "logs/tests", "logs/agents", ".clubs/agents",
    ".clubs/runtime/inbox", ".clubs/runtime/outbox", ".clubs/runtime/state",
    ".clubs/runtime/locks", ".clubs/runtime/events", ".clubs/missions", ".clubs/schemas",
)


def _default_agents() -> dict[str, AgentConfig]:
    return patterns.planner_developer_reviewer_coordinator(DEFAULT_ROLE_IDS)


@dataclass(frozen=True)
class InitAnswers:
    club_name: str
    repository_root: Path
    main_branch: str
    master_contract: str = "MASTER_CONTRACT.md"
    project_type: str = "software-development"
    workflow_pattern: str = DEFAULT_WORKFLOW
    agents: dict[str, AgentConfig] = field(default_factory=_default_agents)


def normalize_relative_path(value: str) -> str:
    """Normalize Windows or Unix input to a safe repository-relative path."""
    normalized = value.strip().replace("\\", "/")
    path = PurePosixPath(normalized)
    if not normalized or path.is_absolute() or ".." in path.parts or path.name in {"", "."}:
        raise InitializationError("Master Contract path must be a non-empty repository-relative path.")
    return path.as_posix()


def build_config(answers: InitAnswers) -> ClubConfig:
    """Build and validate the default 0.1.0 club configuration."""
    if answers.project_type != "software-development":
        raise InitializationError("Version 0.1.0 supports only project type 'software-development'.")
    if not answers.club_name.strip():
        raise InitializationError("Club name cannot be empty.")
    if not answers.main_branch.strip():
        raise InitializationError("Main branch cannot be empty.")
    if not answers.agents:
        raise InitializationError("At least one agent role is required.")
    for role_id in answers.agents:
        if not ROLE_NAME.fullmatch(role_id):
            raise InitializationError("Role names must use lowercase letters, digits, and hyphens.")

    return ClubConfig(
        club=ClubDetails(name=answers.club_name.strip()),
        repository=RepositoryConfig(
            root=".", main_branch=answers.main_branch.strip(),
            master_contract=normalize_relative_path(answers.master_contract),
        ),
        workflow=WorkflowConfig(pattern=answers.workflow_pattern),
        agents=dict(answers.agents),
    )


def _generated_files(config: ClubConfig) -> dict[str, str]:
    files = {
        ".clubs/club.yaml": yaml.safe_dump(
            config.model_dump(mode="json"), sort_keys=False, allow_unicode=True
        )
    }
    for relative_path, template_name in DOCUMENT_TEMPLATES.items():
        target = config.repository.master_contract if relative_path == "MASTER_CONTRACT.md" else relative_path
        files[target] = render_template(template_name, club_name=config.club.name)
    return files


def _existing_targets(root: Path, targets: Iterable[str]) -> list[Path]:
    return [root / relative_path for relative_path in targets if (root / relative_path).exists()]


def initialize_club(answers: InitAnswers, *, force: bool = False) -> ClubConfig:
    """Create the Milestone 2 folder structure without silent overwrites."""
    root = answers.repository_root.expanduser().resolve()
    if not root.exists():
        raise InitializationError(f"Repository root does not exist: {root}")
    if not root.is_dir():
        raise InitializationError(f"Repository root is not a directory: {root}")

    config = build_config(answers)
    files = _generated_files(config)
    existing = _existing_targets(root, files)
    if existing and not force:
        relative = ", ".join(path.relative_to(root).as_posix() for path in existing)
        raise InitializationError(
            "Initialization stopped because it would overwrite existing file(s): "
            f"{relative}. Re-run with --force only if you intend to replace them."
        )

    for relative_path in REQUIRED_DIRECTORIES:
        (root / relative_path).mkdir(parents=True, exist_ok=True)
    for relative_path, content in files.items():
        target = root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8", newline="\n")
    return config
