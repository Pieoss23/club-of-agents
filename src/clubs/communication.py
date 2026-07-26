"""Diagnostic ping/pong command for proving live agent-shell communication."""

from __future__ import annotations

import json
import time
from pathlib import Path

import typer
from rich.console import Console

from clubs import messaging, runtime


console = Console()


def _pong_received(root: Path, agent_id: str, ping_id: str) -> bool:
    events_path = root / ".clubs/runtime/events/events.jsonl"
    if not events_path.is_file():
        return False
    for line in events_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (event.get("type") == "communication.pong.received" and event.get("agent_id") == agent_id
                and event.get("ping_id") == ping_id):
            return True
    return False


def ping(
    to_agent: str,
    from_agent: str = typer.Option(..., "--from", help="Configured agent that must receive the PONG."),
    timeout: float = typer.Option(15.0, "--timeout", min=0.1, help="Seconds to wait for the exchange."),
    message: str = typer.Option("communication diagnostic", "--message", help="Short payload echoed in the PONG."),
    path: Path = typer.Option(Path("."), "--path", help="Repository root to operate on."),
) -> None:
    """Verify direct ping/pong communication between two running agent shells."""
    root = path.expanduser().resolve()
    try:
        agents = runtime.load_agents(root)
    except FileNotFoundError as error:
        console.print("[red]No club found here. Run 'club init' first.[/red]")
        raise typer.Exit(code=1) from error
    if from_agent not in agents or to_agent not in agents:
        console.print(f"[red]Both agents must be configured. Known agents: {', '.join(agents)}[/red]")
        raise typer.Exit(code=1)
    if from_agent == to_agent:
        console.print("[red]Choose two different agents for a communication test.[/red]")
        raise typer.Exit(code=1)

    ping_message = messaging.send_message(
        root, from_agent=from_agent, to_agent=to_agent, type="communication.ping",
        payload={"message": message},
    )
    messaging.emit_event(root, "communication.ping.sent", agent_id=from_agent,
                          to_agent=to_agent, ping_id=ping_message.id)
    messaging.route_messages(root)
    console.print(
        f"PING {ping_message.id}: {from_agent} -> {to_agent}. "
        f"Waiting up to {timeout:g}s for both agent shells to complete the exchange..."
    )

    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        messaging.route_messages(root)
        if _pong_received(root, from_agent, ping_message.id):
            console.print(f"[green]PONG received by {from_agent} from {to_agent}: direct communication verified.[/green]")
            return
        time.sleep(0.1)

    console.print(
        f"[red]No PONG received within {timeout:g}s. Start both shells first: "
        f"'club agent start {from_agent}' and 'club agent start {to_agent}'.[/red]"
    )
    raise typer.Exit(code=1)
