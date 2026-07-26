from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from clubs import communication, messaging, runtime
from clubs.adapters.dummy import DummyProvider
from clubs.cli import app
from clubs.initializer import initialize_club

from conftest import make_init_answers as answers


runner = CliRunner()


def test_running_agents_complete_a_ping_pong_exchange(tmp_path: Path) -> None:
    initialize_club(answers(tmp_path))
    ping = messaging.send_message(
        tmp_path, from_agent="planner", to_agent="developer", type="communication.ping",
        payload={"message": "are you there?"},
    )
    messaging.route_messages(tmp_path)

    assert messaging.process_communication_messages(tmp_path, "developer") == 1
    messaging.route_messages(tmp_path)
    assert messaging.process_communication_messages(tmp_path, "planner") == 1

    events = [
        json.loads(line)
        for line in (tmp_path / ".clubs/runtime/events/events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert {(event["type"], event["agent_id"]) for event in events} == {
        ("communication.ping.received", "developer"),
        ("communication.pong.sent", "developer"),
        ("communication.pong.received", "planner"),
    }
    assert events[-1]["ping_id"] == ping.id


def test_agent_ping_command_reports_a_live_exchange(tmp_path: Path, monkeypatch) -> None:
    initialize_club(answers(tmp_path))

    def advance_agents(_: float) -> None:
        runtime.run_agent_tick(tmp_path, "developer", DummyProvider())
        runtime.run_agent_tick(tmp_path, "planner", DummyProvider())

    monkeypatch.setattr(communication.time, "sleep", advance_agents)
    result = runner.invoke(
        app, ["agent", "ping", "developer", "--from", "planner", "--timeout", "1", "--path", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    assert "direct communication verified" in result.output
