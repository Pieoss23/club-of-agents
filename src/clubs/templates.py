"""Loads the versioned document templates bundled with the package."""

from __future__ import annotations

from importlib import resources


DOCUMENT_TEMPLATES = {
    "MASTER_CONTRACT.md": "MASTER_CONTRACT.md",
    "docs/product/PRODUCT_OVERVIEW.md": "PRODUCT_OVERVIEW.md",
    "docs/architecture/SYSTEM_ARCHITECTURE.md": "SYSTEM_ARCHITECTURE.md",
    "docs/delivery/AGENT_OPERATING_MODEL.md": "AGENT_OPERATING_MODEL.md",
    "docs/features/FEATURE_TEMPLATE.md": "FEATURE_TEMPLATE.md",
    "docs/decisions/ADR_TEMPLATE.md": "ADR_TEMPLATE.md",
    "docs/handoffs/HANDOFF_TEMPLATE.md": "HANDOFF_TEMPLATE.md",
    ".clubs/schemas/task.schema.json": "task.schema.json",
}


def render_template(template_name: str, *, club_name: str) -> str:
    """Return a deterministic rendered document from a bundled template."""
    source = resources.files("clubs").joinpath("templates", template_name)
    return source.read_text(encoding="utf-8").replace("{{ club_name }}", club_name)
