"""Mission creation and storage under .clubs/missions/."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from clubs.models import MISSION_PRIORITIES, Mission
from clubs.validator import validate_club

MISSIONS_DIR = ".clubs/missions"
MISSION_ID_PATTERN = re.compile(r"^MISSION-(\d{3,})$")


class MissionError(RuntimeError):
    """Raised when a mission cannot be created."""


def next_mission_id(root: Path) -> str:
    """Return the next sequential mission id, e.g. MISSION-001."""
    missions_dir = root / MISSIONS_DIR
    highest = 0
    if missions_dir.is_dir():
        for path in missions_dir.glob("MISSION-*.json"):
            match = MISSION_ID_PATTERN.fullmatch(path.stem)
            if match:
                highest = max(highest, int(match.group(1)))
    return f"MISSION-{highest + 1:03d}"


def create_mission(root: Path, *, title: str, description: str, priority: str = "medium") -> Mission:
    """Validate the club, then create and persist a new mission."""
    result = validate_club(root)
    if not result.ok:
        details = "; ".join(f"{issue.path}: {issue.message}" for issue in result.issues)
        raise MissionError(f"Club configuration is invalid. Run 'clubs validate' for details. {details}")
    if priority not in MISSION_PRIORITIES:
        raise MissionError(f"Priority must be one of {', '.join(MISSION_PRIORITIES)}, got '{priority}'.")
    title = title.strip()
    description = description.strip()
    if not title:
        raise MissionError("Mission title cannot be empty.")
    if not description:
        raise MissionError("Mission description cannot be empty.")

    mission = Mission(
        id=next_mission_id(root),
        title=title,
        description=description,
        priority=priority,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    missions_dir = root / MISSIONS_DIR
    missions_dir.mkdir(parents=True, exist_ok=True)
    target = missions_dir / f"{mission.id}.json"
    target.write_text(json.dumps(mission.model_dump(), indent=2) + "\n", encoding="utf-8")
    return mission
