"""Communication-only agent loop that never invokes a task provider."""

from __future__ import annotations

import time
from pathlib import Path

import typer
from rich.console import Console

from clubs import messaging, runtime
from clubs.tasks import now_iso


console = Console()


def listen(
    agent_id: str,
    path: Path = typer.Option(Path("."), "--path", help="Repository root to operate on."),
) -> None:
    """Keep one agent shell available for diagnostic communication only."""
    root = path.expanduser().resolve()
    try:
        agents = runtime.load_agents(root)
    except FileNotFoundError as error:
        console.print("[red]No club found here. Run 'club init' first.[/red]")
        raise typer.Exit(code=1) from error
    if agent_id not in agents:
        console.print(f"[red]'{agent_id}' is not a configured agent. Known agents: {', '.join(agents)}[/red]")
        raise typer.Exit(code=1)

    interval = runtime.load_polling_interval(root)
    console.print(
        f"Listening as '{agent_id}' for communication diagnostics only. "
        "No missions or tasks will be processed. Press Ctrl+C to stop."
    )
    try:
        while True:
            runtime.write_state(root, agent_id, status="waiting", last_heartbeat=now_iso())
            messaging.route_messages(root)
            messaging.process_communication_messages(root, agent_id)
            messaging.route_messages(root)
            time.sleep(interval)
    except KeyboardInterrupt:
        runtime.write_state(root, agent_id, status="offline")
        console.print(f"\nListener '{agent_id}' stopped.")
