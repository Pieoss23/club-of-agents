from __future__ import annotations

import json
from pathlib import Path

from clubs import messaging
from clubs.initializer import initialize_club

from conftest import make_init_answers as answers


def test_send_message_writes_to_sender_outbox(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    message = messaging.send_message(tmp_path, from_agent="planner", to_agent="coordinator", type="task.created")
    outbox_file = tmp_path / ".clubs/runtime/outbox/planner" / f"{message.id}.json"
    assert outbox_file.is_file()


def test_route_messages_moves_file_to_recipient_inbox(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    message = messaging.send_message(tmp_path, from_agent="planner", to_agent="coordinator", type="task.created", task_id="TASK-001")
    routed = messaging.route_messages(tmp_path)
    assert routed == 1
    inbox_file = tmp_path / ".clubs/runtime/inbox/coordinator" / f"{message.id}.json"
    assert inbox_file.is_file()
    assert not (tmp_path / ".clubs/runtime/outbox/planner" / f"{message.id}.json").exists()
    payload = json.loads(inbox_file.read_text(encoding="utf-8"))
    assert payload["from"] == "planner"
    assert payload["to"] == "coordinator"


def test_route_messages_is_idempotent_with_nothing_pending(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    assert messaging.route_messages(tmp_path) == 0


def test_emit_event_appends_json_lines(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    messaging.emit_event(tmp_path, "task.created", task_id="TASK-001")
    messaging.emit_event(tmp_path, "task.assigned", task_id="TASK-001", owner="developer")
    lines = (tmp_path / ".clubs/runtime/events/events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["type"] == "task.created"
    assert first["task_id"] == "TASK-001"
