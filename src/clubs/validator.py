"""Validates an initialized club against the 0.1.0 configuration contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml
from pydantic import ValidationError

from clubs.initializer import REQUIRED_DIRECTORIES, ROLE_NAME
from clubs.models import PROVIDER_TYPES, TEXT_ONLY_PROVIDER_TYPES, ClubConfig
from clubs.patterns import PATTERN_IDS

CLUB_YAML_PATH = ".clubs/club.yaml"
TASK_SCHEMA_PATH = ".clubs/schemas/task.schema.json"


@dataclass(frozen=True)
class ValidationIssue:
    path: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    issues: tuple[ValidationIssue, ...]

    @property
    def ok(self) -> bool:
        return not self.issues


def _load_config(root: Path, issues: list[ValidationIssue]) -> ClubConfig | None:
    club_yaml = root / CLUB_YAML_PATH
    if not club_yaml.is_file():
        issues.append(ValidationIssue(CLUB_YAML_PATH, "File does not exist. Run 'clubs init' first."))
        return None
    try:
        raw = yaml.safe_load(club_yaml.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        issues.append(ValidationIssue(CLUB_YAML_PATH, f"Invalid YAML: {error}"))
        return None
    try:
        return ClubConfig.model_validate(raw)
    except ValidationError as error:
        for err in error.errors():
            field = ".".join(str(part) for part in err["loc"]) or CLUB_YAML_PATH
            issues.append(ValidationIssue(field, err["msg"]))
        return None


def validate_club(root: Path) -> ValidationResult:
    """Check a club's configuration, documents, and folder structure."""
    issues: list[ValidationIssue] = []
    config = _load_config(root, issues)
    if config is None:
        return ValidationResult(tuple(issues))

    if config.workflow.pattern not in PATTERN_IDS:
        issues.append(ValidationIssue(
            "workflow.pattern",
            f"Unknown collaboration pattern '{config.workflow.pattern}'. "
            f"Supported patterns: {', '.join(PATTERN_IDS)}.",
        ))

    for role_id, agent in config.agents.items():
        if not ROLE_NAME.fullmatch(role_id):
            issues.append(ValidationIssue(f"agents.{role_id}", "Role names must use lowercase letters, digits, and hyphens."))
        if agent.provider not in PROVIDER_TYPES:
            issues.append(ValidationIssue(
                f"agents.{role_id}.provider",
                f"Unknown provider '{agent.provider}'. Supported: {', '.join(PROVIDER_TYPES)}.",
            ))
        if agent.provider == "shell" and not agent.provider_command:
            issues.append(ValidationIssue(
                f"agents.{role_id}.provider_command", "provider 'shell' requires provider_command to be set.",
            ))
        if agent.can_code and agent.provider in TEXT_ONLY_PROVIDER_TYPES:
            issues.append(ValidationIssue(
                f"agents.{role_id}.provider",
                f"'{agent.provider}' has no file-editing agency and cannot back can_code. "
                "Use dummy, shell, claude, or codex instead.",
            ))
        if agent.can_bootstrap and agent.provider not in TEXT_ONLY_PROVIDER_TYPES:
            issues.append(ValidationIssue(
                f"agents.{role_id}.can_bootstrap",
                f"can_bootstrap is only implemented for {', '.join(TEXT_ONLY_PROVIDER_TYPES)} "
                f"(got '{agent.provider}').",
            ))

    if not (root / config.repository.master_contract).is_file():
        issues.append(ValidationIssue(config.repository.master_contract, "Master Contract file is missing."))

    if not (root / TASK_SCHEMA_PATH).is_file():
        issues.append(ValidationIssue(TASK_SCHEMA_PATH, "Task schema file is missing."))

    for field_name, relative_path in (
        ("documentation.product", config.documentation.product),
        ("documentation.architecture", config.documentation.architecture),
        ("documentation.delivery", config.documentation.delivery),
    ):
        if not (root / relative_path).is_file():
            issues.append(ValidationIssue(relative_path, f"Document referenced by {field_name} is missing."))

    for relative_path in REQUIRED_DIRECTORIES:
        if not (root / relative_path).is_dir():
            issues.append(ValidationIssue(relative_path, "Required directory is missing."))

    return ValidationResult(tuple(issues))
