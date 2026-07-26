"""The public command line interface for Clubs of Agents."""

from __future__ import annotations

import json
import time
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from clubs import __version__, banner, interactive, patterns, runtime, tasks
from clubs.adapters.dummy import DummyProvider
from clubs.initializer import InitAnswers, InitializationError, initialize_club
from clubs.missions import MissionError, create_mission
from clubs.models import AgentConfig, DEFAULT_ROLE_IDS, MISSION_PRIORITIES
from clubs.status import StatusError, collect_status
from clubs.validator import validate_club


app = typer.Typer(name="club", help="Create structured, durable multi-agent development environments.", no_args_is_help=False, add_completion=False)
agent_app = typer.Typer(name="agent", help="Inspect and manage club agents.", add_completion=False)
mission_app = typer.Typer(name="mission", help="Create and manage missions.", add_completion=False)
task_app = typer.Typer(name="task", help="Create and inspect tasks.", add_completion=False)
app.add_typer(agent_app, name="agent")
app.add_typer(mission_app, name="mission")
app.add_typer(task_app, name="task")
console = Console()
PATH_OPTION = typer.Option(Path("."), "--path", help="Repository root to operate on.")
ROLE_NAME_SUGGESTIONS = [*DEFAULT_ROLE_IDS, "architect", "backend", "frontend", "tester", "security", "devops"]


def _prompt_project_type() -> str:
    project_type = typer.prompt("Project type", default="software-development").strip()
    if project_type != "software-development":
        raise typer.BadParameter("Version 0.1.0 supports only 'software-development'.")
    return project_type


def _choose_pattern() -> str:
    choices = [(pattern_id, patterns.PATTERN_LABELS[pattern_id]) for pattern_id in patterns.PATTERN_IDS]
    return interactive.select_one(
        "Collaboration pattern", choices, default=patterns.PLANNER_DEVELOPER_REVIEWER_COORDINATOR,
    )


def _prompt_roles() -> tuple[str, ...]:
    count = typer.prompt("Number of agent shells", default=4, type=int)
    if count < 1:
        raise typer.BadParameter("At least one agent shell is required.")
    roles: list[str] = []
    for position in range(count):
        default = DEFAULT_ROLE_IDS[position] if position < len(DEFAULT_ROLE_IDS) else f"agent-{position + 1}"
        role = interactive.text(f"Role for shell {position + 1}", default=default, suggestions=ROLE_NAME_SUGGESTIONS)
        roles.append(role.strip())
    return tuple(roles)


def _prompt_worker_count() -> int:
    count = typer.prompt("Number of workers", default=2, type=int)
    if count < 1:
        raise typer.BadParameter("At least one worker is required.")
    return count


def _prompt_components() -> tuple[str, ...]:
    return tuple(interactive.text_loop("Component name"))


def _prompt_custom_roles() -> tuple[tuple[str, tuple[str, ...]], ...]:
    console.print("Define custom roles. Leave the role name blank to finish (at least one required).")
    role_capabilities: list[tuple[str, tuple[str, ...]]] = []
    while True:
        role_name = interactive.text("Role name", suggestions=ROLE_NAME_SUGGESTIONS).strip()
        if not role_name:
            if not role_capabilities:
                raise typer.BadParameter("At least one custom role is required.")
            return tuple(role_capabilities)
        capabilities = interactive.checkbox(
            f"Capabilities for '{role_name}'", list(patterns.CAPABILITY_FIELDS),
        )
        role_capabilities.append((role_name, tuple(capabilities)))


def _build_agents_for_pattern(pattern_id: str) -> dict[str, AgentConfig]:
    if pattern_id == patterns.PLANNER_DEVELOPER_REVIEWER_COORDINATOR:
        return patterns.planner_developer_reviewer_coordinator(_prompt_roles())
    if pattern_id == patterns.MASTER_WORKERS:
        return patterns.master_workers(_prompt_worker_count())
    if pattern_id == patterns.ARCHITECT_FRONTEND_BACKEND_REVIEWER:
        return patterns.architect_frontend_backend_reviewer()
    if pattern_id == patterns.SWARM_BY_COMPONENT:
        return patterns.swarm_by_component(_prompt_components())
    if pattern_id == patterns.CUSTOM:
        return patterns.custom(_prompt_custom_roles())
    raise typer.BadParameter(f"Unknown pattern '{pattern_id}'.")


def _prompt_master_contract() -> str:
    console.print("Master Contract location:")
    console.print("  1. Repository root [default]\n  2. docs/governance/\n  3. .clubs/context/\n  4. Custom path")
    choice = typer.prompt("Choose a location", default="1").strip()
    locations = {"1": "MASTER_CONTRACT.md", "2": "docs/governance/MASTER_CONTRACT.md", "3": ".clubs/context/MASTER_CONTRACT.md"}
    if choice == "4":
        return typer.prompt("Custom Master Contract path", default="MASTER_CONTRACT.md")
    if choice not in locations:
        raise typer.BadParameter("Choose a number from 1 to 4.")
    return locations[choice]


def collect_answers(*, root: Path | None = None) -> InitAnswers:
    """Ask every wizard question and return raw answers."""
    default_name = (root or Path.cwd()).resolve().name or "my-club"
    club_name = typer.prompt("Club name", default=default_name)
    project_type = _prompt_project_type()
    chosen_root = root or Path(typer.prompt("Repository root", default=".")).expanduser()
    main_branch = interactive.text("Main branch", default="main", suggestions=["main", "master", "develop"])
    pattern_id = _choose_pattern()
    agents = _build_agents_for_pattern(pattern_id)
    master_contract = _prompt_master_contract()
    return InitAnswers(club_name=club_name, project_type=project_type, repository_root=chosen_root,
                       main_branch=main_branch, workflow_pattern=pattern_id, agents=agents,
                       master_contract=master_contract)


@app.callback(invoke_without_command=True)
def root_command(ctx: typer.Context, version: bool = typer.Option(False, "--version", help="Show the installed CoA version.")) -> None:
    """Show the first-run menu when `club` has no subcommand."""
    if version:
        console.print(__version__)
        raise typer.Exit()
    if ctx.invoked_subcommand is None:
        _show_menu()


def _show_menu() -> None:
    console.print("[bold]Clubs of Agents[/bold]\n")
    table = Table(show_header=False, box=None, padding=(0, 1))
    for number, label in (("1", "Create a new club"), ("2", "Open an existing club"),
                          ("3", "Validate club configuration"), ("4", "Show club status"),
                          ("5", "List agents"), ("6", "Start an agent"), ("7", "Exit")):
        table.add_row(number + ".", label)
    console.print(table)
    selection = typer.prompt("Select an option", default="7").strip()
    if selection == "1":
        _run_init(force=False)
    elif selection == "3":
        _run_validate(Path("."))
    elif selection == "4":
        _run_status(Path("."))
    elif selection == "5":
        _run_agent_list(Path("."))
    elif selection == "6":
        try:
            agents = runtime.load_agents(Path("."))
        except FileNotFoundError:
            console.print("[red]No club found here. Run 'club init' first.[/red]")
            return
        agent_id = interactive.select_one(
            "Agent to start", [(agent_id, f"{agent_id} ({config.role})") for agent_id, config in agents.items()],
            default=next(iter(agents), ""),
        )
        _run_agent_start(agent_id, Path("."))
    elif selection != "7":
        console.print("That action is planned for a later milestone.")


def _run_init(*, force: bool) -> None:
    try:
        config = initialize_club(collect_answers(), force=force)
    except (InitializationError, typer.BadParameter) as error:
        console.print(f"[red]Initialization failed:[/red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]Club '{config.club.name}' created successfully.[/green]")
    console.print("Generated .clubs/club.yaml, the document pyramid, task folders, and runtime folders.")
    console.print("Next: run 'club agent start <agent-id>' in one shell per role.")
    if interactive.is_interactive():
        banner.play_intro_animation(console)


@app.command()
def init(force: bool = typer.Option(False, "--force", help="Explicitly overwrite CoA-generated files.")) -> None:
    """Launch the interactive wizard and create a club in the chosen repository."""
    _run_init(force=force)


def _run_validate(path: Path) -> None:
    root = path.expanduser().resolve()
    result = validate_club(root)
    table = Table("Check", "Status")
    if result.ok:
        table.add_row("Configuration, documents, and folders", "[green]OK[/green]")
    else:
        for issue in result.issues:
            table.add_row(issue.path, f"[red]{issue.message}[/red]")
    console.print(table)
    if not result.ok:
        raise typer.Exit(code=1)


@app.command()
def validate(path: Path = PATH_OPTION) -> None:
    """Check a club's configuration, documents, and folder structure."""
    _run_validate(path)


def _run_status(path: Path) -> None:
    root = path.expanduser().resolve()
    try:
        snapshot = collect_status(root)
    except StatusError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error

    console.print(f"[bold]{snapshot.club_name}[/bold] — {snapshot.workflow_pattern}\n")

    agents_table = Table("Role", "Agent ID", "State", "Current Task")
    for agent in snapshot.agents:
        agents_table.add_row(agent.role, agent.agent_id, agent.state, agent.current_task_id or "-")
    console.print(agents_table)

    tasks_table = Table("Backlog", "Active", "Review", "Blocked", "Done", "Missions")
    tasks_table.add_row(
        str(snapshot.tasks.backlog), str(snapshot.tasks.active), str(snapshot.tasks.review),
        str(snapshot.tasks.blocked), str(snapshot.tasks.done), str(snapshot.missions),
    )
    console.print(tasks_table)


@app.command()
def status(path: Path = PATH_OPTION) -> None:
    """Show the current agents, task counts, and missions for a club."""
    _run_status(path)


def _run_agent_list(path: Path) -> None:
    root = path.expanduser().resolve()
    try:
        snapshot = collect_status(root)
    except StatusError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(code=1) from error
    table = Table("Role", "Agent ID", "State", "Current Task")
    for agent in snapshot.agents:
        table.add_row(agent.role, agent.agent_id, agent.state, agent.current_task_id or "-")
    console.print(table)


@agent_app.command("list")
def agent_list(path: Path = PATH_OPTION) -> None:
    """List every configured agent and its current state."""
    _run_agent_list(path)


def _run_agent_start(agent_id: str, path: Path) -> None:
    root = path.expanduser().resolve()
    try:
        agents = runtime.load_agents(root)
    except FileNotFoundError as error:
        console.print("[red]No club found here. Run 'club init' first.[/red]")
        raise typer.Exit(code=1) from error
    if agent_id not in agents:
        console.print(f"[red]'{agent_id}' is not a configured agent. Known agents: {', '.join(agents)}[/red]")
        raise typer.Exit(code=1)

    console.print(
        f"Starting agent '{agent_id}' ({agents[agent_id].role}). Uses the dummy provider "
        "(mechanical bookkeeping only, no real code generation yet). Press Ctrl+C to stop."
    )
    provider = DummyProvider(work_seconds=1.5)
    interval = runtime.load_polling_interval(root)
    try:
        while True:
            runtime.run_agent_tick(root, agent_id, provider)
            time.sleep(interval)
    except KeyboardInterrupt:
        runtime.write_state(root, agent_id, status="offline")
        console.print(f"\nAgent '{agent_id}' stopped.")


@agent_app.command("start")
def agent_start(agent_id: str, path: Path = PATH_OPTION) -> None:
    """Run one agent's poll loop until Ctrl+C. Uses the dummy provider (no real code generation yet)."""
    _run_agent_start(agent_id, path)


def _run_mission_create(path: Path) -> None:
    root = path.expanduser().resolve()
    title = typer.prompt("Mission title")
    description = typer.prompt("Description")
    priority = interactive.select_one(
        "Priority", [(value, value) for value in MISSION_PRIORITIES], default="medium",
    )
    try:
        mission = create_mission(root, title=title, description=description, priority=priority)
    except MissionError as error:
        console.print(f"[red]Mission creation failed:[/red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]Mission '{mission.id}' created.[/green]")


@mission_app.command("create")
def mission_create(path: Path = PATH_OPTION) -> None:
    """Create a new mission interactively."""
    _run_mission_create(path)


def _run_task_create(path: Path) -> None:
    root = path.expanduser().resolve()
    missions_dir = root / ".clubs/missions"
    mission_files = sorted(missions_dir.glob("MISSION-*.json")) if missions_dir.is_dir() else []
    if not mission_files:
        console.print("[red]No missions found. Run 'club mission create' first.[/red]")
        raise typer.Exit(code=1)

    choices = []
    for mission_path in mission_files:
        mission = json.loads(mission_path.read_text(encoding="utf-8"))
        choices.append((mission["id"], f"{mission['id']} - {mission['title']}"))
    mission_id = interactive.select_one("Mission", choices, default=choices[0][0])
    title = typer.prompt("Task title")
    objective = typer.prompt("Objective")
    priority = interactive.select_one(
        "Priority", [(value, value) for value in MISSION_PRIORITIES], default="medium",
    )

    try:
        task = tasks.create_task(root, mission_id=mission_id, title=title, objective=objective, priority=priority)
    except tasks.TaskError as error:
        console.print(f"[red]Task creation failed:[/red] {error}")
        raise typer.Exit(code=1) from error

    mission_path = missions_dir / f"{mission_id}.json"
    mission = json.loads(mission_path.read_text(encoding="utf-8"))
    mission.setdefault("tasks", [])
    if task["id"] not in mission["tasks"]:
        mission["tasks"].append(task["id"])
    mission_path.write_text(json.dumps(mission, indent=2) + "\n", encoding="utf-8")

    console.print(f"[green]Task '{task['id']}' created in backlog.[/green]")


@task_app.command("create")
def task_create(path: Path = PATH_OPTION) -> None:
    """Create a new task under an existing mission, interactively."""
    _run_task_create(path)


def _run_task_list(stage: str | None, path: Path) -> None:
    root = path.expanduser().resolve()
    if stage is not None and stage not in tasks.TASK_STAGES:
        console.print(f"[red]Stage must be one of: {', '.join(tasks.TASK_STAGES)}[/red]")
        raise typer.Exit(code=1)

    table = Table("ID", "Stage", "Title", "Status", "Owner")
    for current_stage in ((stage,) if stage else tasks.TASK_STAGES):
        stage_dir = root / "tasks" / current_stage
        if not stage_dir.is_dir():
            continue
        for task_path in sorted(stage_dir.glob("TASK-*.json")):
            task = tasks.load_task(task_path)
            owner = (task.get("owner") or {}).get("agent_id", "-")
            table.add_row(task["id"], current_stage, task["title"], task["status"], owner)
    console.print(table)


@task_app.command("list")
def task_list(
    stage: str = typer.Option(None, "--stage", help="Filter by one stage (backlog/active/review/blocked/done)."),
    path: Path = PATH_OPTION,
) -> None:
    """List tasks across all stages, or one stage with --stage."""
    _run_task_list(stage, path)


def _run_task_show(task_id: str, path: Path) -> None:
    root = path.expanduser().resolve()
    found = tasks.find_task_by_id(root, task_id)
    if found is None:
        console.print(f"[red]Task '{task_id}' was not found in any stage.[/red]")
        raise typer.Exit(code=1)
    stage, task = found
    console.print(f"[bold]{task_id}[/bold] (stage: {stage})\n")
    console.print_json(data=task)


@task_app.command("show")
def task_show(task_id: str, path: Path = PATH_OPTION) -> None:
    """Show a task's full JSON, wherever it currently is."""
    _run_task_show(task_id, path)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
