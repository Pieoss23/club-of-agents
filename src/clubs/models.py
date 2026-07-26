"""Typed, provider-independent models used by the initialization flow."""

from __future__ import annotations

from pydantic import BaseModel, Field


DEFAULT_ROLE_IDS = ("planner", "developer", "reviewer", "coordinator")
DEFAULT_WORKFLOW = "planner-developer-reviewer-coordinator"


class AgentConfig(BaseModel):
    role: str
    shell: str = "dedicated"
    can_plan: bool = False
    can_code: bool = False
    can_review: bool = False
    can_assign: bool = False
    can_merge: bool = False


class ClubDetails(BaseModel):
    name: str = Field(min_length=1)
    type: str = "software-development"


class RepositoryConfig(BaseModel):
    root: str = "."
    main_branch: str = Field(min_length=1)
    master_contract: str = Field(min_length=1)


class DocumentationConfig(BaseModel):
    product: str = "docs/product/PRODUCT_OVERVIEW.md"
    architecture: str = "docs/architecture/SYSTEM_ARCHITECTURE.md"
    delivery: str = "docs/delivery/AGENT_OPERATING_MODEL.md"
    features: str = "docs/features"
    decisions: str = "docs/decisions"
    handoffs: str = "docs/handoffs"


class RuntimeConfig(BaseModel):
    communication: str = "filesystem"
    polling_interval_seconds: int = 3
    heartbeat_interval_seconds: int = 10
    heartbeat_timeout_seconds: int = 60
    max_tasks_per_agent: int = 1


class WorkflowConfig(BaseModel):
    pattern: str = DEFAULT_WORKFLOW


class ClubConfig(BaseModel):
    version: int = 1
    club: ClubDetails
    repository: RepositoryConfig
    documentation: DocumentationConfig = Field(default_factory=DocumentationConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    workflow: WorkflowConfig = Field(default_factory=WorkflowConfig)
    agents: dict[str, AgentConfig]


MISSION_PRIORITIES = ("low", "medium", "high", "critical")


class Mission(BaseModel):
    id: str = Field(pattern=r"^MISSION-\d{3,}$")
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: str = "medium"
    status: str = "planning"
    created_at: str
    assigned_to: str = "planner"
    tasks: list[str] = Field(default_factory=list)
