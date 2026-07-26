# Clubs of Agents (`club`)

A local, provider-agnostic CLI that turns a normal Git repository into a structured
multi-agent development environment: a shared `club.yaml`, a document pyramid, a
filesystem message bus, Git worktree isolation per task, and pluggable "provider"
adapters (a safe mechanical dummy, a generic shell script, Claude Code, or Codex) that
actually do the planning/implementing/reviewing.

The repository is the durable shared memory. Nothing here depends on a database, a
web dashboard, or a specific LLM vendor — see `docs/cli/architecture.md`.

## Quickstart

```bash
pip install -e .
club init          # interactive wizard: name, collaboration pattern, roles, Master Contract location
club validate       # check the generated config/docs/folders
club mission create # describe a goal in one sentence
club task create    # decompose it into a task under that mission
club agent start developer   # run one agent's poll loop (dummy provider by default)
club status         # see agents, task counts, missions at a glance
```

Full walkthrough: [docs/cli/quickstart.md](docs/cli/quickstart.md).

## Documentation

- [docs/cli/installation.md](docs/cli/installation.md) — requirements, editable install, verifying the `club` command.
- [docs/cli/quickstart.md](docs/cli/quickstart.md) — a full lifecycle, start to finish.
- [docs/cli/commands.md](docs/cli/commands.md) — every command and flag.
- [docs/cli/configuration.md](docs/cli/configuration.md) — `club.yaml` reference.
- [docs/cli/patterns.md](docs/cli/patterns.md) — the 5 collaboration patterns and the roles/capabilities each one generates.
- [docs/cli/workflow.md](docs/cli/workflow.md) — the task lifecycle, Git isolation, path policy, PR drafts.
- [docs/cli/providers.md](docs/cli/providers.md) — dummy/shell/Claude/Codex adapters, including the real, unattended-execution safety notes.
- [docs/cli/architecture.md](docs/cli/architecture.md) — module map and contributor guide.

## Project status

All 10 milestones from the original design brief are implemented: CLI skeleton, init
wizard, validation, status, missions/tasks, the filesystem message bus, the agent
runner, the stage-transition workflow engine, Git worktree isolation, and provider
adapters (shell/Claude/Codex). See `python -m pytest -q` (123 tests) for the current
regression suite.

## The dogfooded example project

Before this CLI existed, this same repository was used to prove out its document/task
conventions by hand — a small Node.js health-check HTTP service built via simulated
planner/developer/reviewer agents. That history (and how to run it) is preserved in
[docs/dogfood-example.md](docs/dogfood-example.md); it's a real example of the workflow
`club` now automates, not part of the CLI itself.

## License

MIT — see [LICENSE](LICENSE).
