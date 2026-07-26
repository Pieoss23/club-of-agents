"""Writes an auditable prompt/response transcript for every real provider invocation.

Uses logs/agents/, a directory every club already has (src/clubs/initializer.py's
REQUIRED_DIRECTORIES) but that nothing wrote to before real providers existed.
"""

from __future__ import annotations

from pathlib import Path


def write_log(root: Path, agent_id: str, item_id: str, capability: str, *, prompt: str, stdout: str, stderr: str) -> Path:
    log_dir = root / "logs/agents" / agent_id
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{item_id}-{capability}.log"
    log_path.write_text(
        f"=== PROMPT ===\n{prompt}\n\n=== STDOUT ===\n{stdout}\n\n=== STDERR ===\n{stderr}\n",
        encoding="utf-8",
    )
    return log_path
