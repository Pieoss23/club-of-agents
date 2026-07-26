"""Shared prompt assembly for every real (LLM-backed) provider adapter.

Reuses this project's own established voice: the generated Master Contract
(club constitution) and the task contract fields already defined by tasks.py /
schemas/task.schema.json, rather than inventing a separate prompting style.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml


def read_master_contract(root: Path) -> str:
    """The club's Master Contract text, or '' if it can't be found."""
    club_yaml = root / ".clubs/club.yaml"
    if not club_yaml.is_file():
        return ""
    raw = yaml.safe_load(club_yaml.read_text(encoding="utf-8"))
    contract_path = root / raw["repository"]["master_contract"]
    return contract_path.read_text(encoding="utf-8") if contract_path.is_file() else ""


def plan_prompt(master_contract: str, mission: dict) -> str:
    return (
        f"{master_contract}\n\n"
        "You are the planner. Decompose the mission below into exactly one task "
        "(a later planning pass can add more). Respond with nothing but a single JSON "
        'object: {"title": "<short task title>", "objective": "<one clear sentence>"}.\n\n'
        f"Mission title: {mission['title']}\n"
        f"Mission description: {mission['description']}\n"
    )


def implement_prompt(master_contract: str, task: dict) -> str:
    criteria = "\n".join(f"- {c['description']}" for c in task["acceptance_criteria"])
    notes = task.get("notes") or []
    notes_block = (
        "\n\nPrior notes (read these -- if any are review findings, this is a rework, fix them):\n"
        + "\n".join(f"- {note}" for note in notes)
    ) if notes else ""
    return (
        f"{master_contract}\n\n"
        f"You are implementing task {task['id']}: {task['title']}.\n\n"
        f"Objective: {task['objective']}\n\n"
        f"Acceptance criteria:\n{criteria}\n\n"
        f"Allowed paths: {', '.join(task['allowed_paths'])}\n"
        f"Forbidden paths: {', '.join(task['forbidden_paths']) or '(none)'}\n"
        f"{notes_block}\n\n"
        "Implement the task, add tests, and stay strictly within the allowed paths. "
        "Do not touch forbidden paths. Do not expand the task's scope."
    )


def review_prompt(master_contract: str, task: dict, diff: str) -> str:
    criteria = "\n".join(f"- {c['description']}" for c in task["acceptance_criteria"])
    return (
        f"{master_contract}\n\n"
        f"You are reviewing task {task['id']}: {task['title']}.\n\n"
        f"Objective: {task['objective']}\n\n"
        f"Acceptance criteria:\n{criteria}\n\n"
        f"Diff to review:\n```diff\n{diff}\n```\n\n"
        "Verify the diff actually satisfies every acceptance criterion and does not "
        "silently expand scope. Respond with nothing but a single JSON object: "
        '{"approved": true|false, "findings": ["<finding>", ...]} (empty findings list if approved).'
    )


def configure_prompt(master_contract: str, mission: dict, capability_labels: list[str]) -> str:
    return (
        f"{master_contract}\n\n"
        "You are bootstrapping a fresh multi-agent club for the project described below. "
        "Decide how many agent roles are needed and what each one can do.\n\n"
        f"Available capabilities: {', '.join(capability_labels)} "
        "(plan=decompose missions into tasks, code=implement tasks, review=approve/reject "
        "reviews, assign=assign backlog tasks to a free capable agent, merge=integrate "
        "approved tasks into done).\n\n"
        f"Project title: {mission['title']}\n"
        f"Project description: {mission['description']}\n\n"
        "Respond with nothing but a single JSON object: "
        '{"roles": [{"id": "<lowercase-hyphen-role-name>", "capabilities": ["plan", "code", ...]}, ...]}. '
        "Include at least one role with 'assign' and one with 'merge', or tasks will never reach done."
    )


def parse_json_response(text: str) -> dict:
    """Best-effort JSON extraction: the whole response, or the first {...} block in it."""
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"No JSON object found in response: {text[:200]!r}")
