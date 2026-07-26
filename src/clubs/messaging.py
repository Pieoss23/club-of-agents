"""Filesystem message bus: outbox -> inbox routing and the shared event log."""

from __future__ import annotations

import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str
    from_agent: str = Field(alias="from")
    to_agent: str = Field(alias="to")
    type: str
    task_id: str | None = None
    timestamp: str
    payload: dict = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


@contextmanager
def _file_lock(root: Path, name: str, *, timeout: float = 5.0) -> Iterator[None]:
    """A minimal cross-platform exclusive lock using atomic file creation."""
    lock_path = root / ".clubs/runtime/locks" / f"{name}.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            break
        except FileExistsError:
            if time.monotonic() > deadline:
                raise TimeoutError(f"Could not acquire lock '{name}' within {timeout}s")
            time.sleep(0.05)
    try:
        yield
    finally:
        lock_path.unlink(missing_ok=True)


def send_message(
    root: Path, *, from_agent: str, to_agent: str, type: str,
    task_id: str | None = None, payload: dict | None = None,
) -> Message:
    """Write a message to the sender's outbox for later routing."""
    message = Message(
        id=f"MSG-{uuid.uuid4().hex[:12]}", **{"from": from_agent, "to": to_agent},
        type=type, task_id=task_id, timestamp=datetime.now(timezone.utc).isoformat(),
        payload=payload or {},
    )
    outbox_dir = root / ".clubs/runtime/outbox" / from_agent
    outbox_dir.mkdir(parents=True, exist_ok=True)
    (outbox_dir / f"{message.id}.json").write_text(
        json.dumps(message.model_dump(by_alias=True), indent=2) + "\n", encoding="utf-8"
    )
    return message


def route_messages(root: Path) -> int:
    """Move every pending outbox message into its recipient's inbox. Returns the count routed."""
    outbox_root = root / ".clubs/runtime/outbox"
    if not outbox_root.is_dir():
        return 0
    routed = 0
    for agent_outbox in outbox_root.iterdir():
        if not agent_outbox.is_dir():
            continue
        for message_path in agent_outbox.glob("*.json"):
            try:
                raw = json.loads(message_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            to_agent = raw.get("to")
            if not to_agent:
                continue
            inbox_dir = root / ".clubs/runtime/inbox" / to_agent
            inbox_dir.mkdir(parents=True, exist_ok=True)
            try:
                message_path.rename(inbox_dir / message_path.name)
            except FileNotFoundError:
                continue
            routed += 1
    return routed


def process_communication_messages(root: Path, agent_id: str) -> int:
    """Handle diagnostic ping/pong messages addressed to one running agent.

    This deliberately handles only the ``communication.*`` protocol. Workflow
    messages remain durable in the inbox for their normal consumers. A processed
    diagnostic message is renamed with a non-JSON suffix, preventing a poll loop
    from replying to the same ping more than once.
    """
    inbox_dir = root / ".clubs/runtime/inbox" / agent_id
    if not inbox_dir.is_dir():
        return 0

    handled = 0
    for message_path in inbox_dir.glob("*.json"):
        try:
            message = Message.model_validate_json(message_path.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if message.to_agent != agent_id or message.type not in {"communication.ping", "communication.pong"}:
            continue

        try:
            message_path.rename(message_path.with_suffix(".handled"))
        except FileNotFoundError:
            continue

        if message.type == "communication.ping":
            emit_event(root, "communication.ping.received", agent_id=agent_id, ping_id=message.id,
                       from_agent=message.from_agent)
            pong = send_message(
                root, from_agent=agent_id, to_agent=message.from_agent,
                type="communication.pong",
                payload={"ping_id": message.id, "message": message.payload.get("message", "")},
            )
            emit_event(root, "communication.pong.sent", agent_id=agent_id, ping_id=message.id,
                       pong_id=pong.id, to_agent=message.from_agent)
        else:
            emit_event(root, "communication.pong.received", agent_id=agent_id,
                       ping_id=message.payload.get("ping_id"), from_agent=message.from_agent,
                       pong_id=message.id)

        handled += 1
    return handled

def emit_event(root: Path, event_type: str, **payload: object) -> None:
    """Append one JSON line to the shared event log, guarded by a file lock."""
    entry = {"type": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), **payload}
    events_dir = root / ".clubs/runtime/events"
    events_dir.mkdir(parents=True, exist_ok=True)
    with _file_lock(root, "events"):
        with open(events_dir / "events.jsonl", "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry) + "\n")
