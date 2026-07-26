# Changelog

All notable changes to this project are documented here. Format loosely follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-07-26

### Added

- `club` CLI skeleton (`club`, `club --version`, `club --help`) and the interactive
  first-run menu.
- `club init` wizard: club name, project type, repository root/main branch, 5
  collaboration patterns (planner/developer/reviewer/coordinator, master/workers,
  architect/frontend/backend/reviewer, swarm by component, custom), Master Contract
  location, and the generated document pyramid, task folders, and runtime folders.
  Never silently overwrites existing files (`--force` required).
- `club validate` and `club status` — configuration/document/folder checks and a
  live snapshot of agents, task counts, and missions.
- `club mission create` and `club task create/list/show` — mission and task
  lifecycle management, validated against the bundled task schema.
- Filesystem message bus (`.clubs/runtime/{inbox,outbox,events}`) and agent-to-agent
  direct communication (`club agent ping`).
- `club agent start` — the per-agent poll loop (heartbeat, message routing,
  capability-driven work), backed by `runtime.run_agent_tick`.
- `workflow.py` stage-transition engine: `assign_task` → `submit_for_review` →
  `approve_review`/`reject_review` → `integrate`, all provider-agnostic.
- Git worktree isolation per assigned task (sibling directory, dedicated branch),
  automatic commit tracking, warn-only path-policy checks against a task's
  allowed/forbidden paths, and local pull-request draft preparation
  (`docs/handoffs/{task-id}-pr-draft.md`) — no network calls, nothing pushed.
- `club task cleanup` — removes the worktree/branch for done tasks, with a
  confirmation prompt (`--yes` to skip it).
- Provider adapters: `dummy` (mechanical, default, no real code generation), `shell`
  (fully generic, invokes any user script), `claude` (Claude Code headless), `codex`
  (Codex CLI headless). Every real-provider invocation is logged to
  `logs/agents/<agent-id>/` and can fail without crashing the poll loop
  (`ProviderError` handling in `runtime.run_agent_tick`).
- Task rejection/rework loop: a real reviewer that doesn't approve sends the task
  back to `active` for the same owner, with findings recorded as notes and surfaced
  in the next `implement` prompt.
- Full documentation set under `docs/cli/` (installation, quickstart, commands,
  configuration, patterns, workflow, providers, architecture) and a rewritten
  top-level `README.md`.
- 132 passing tests; no test ever invokes a real `claude`/`codex`/shell subprocess —
  every real-provider test injects a fake subprocess call.

### Notes

- No PyPI release yet — this version lives in the repository only.
