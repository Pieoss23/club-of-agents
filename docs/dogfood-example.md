# Dogfood example: the original manual multi-agent project

Before the `club` CLI existed, this repository was used to prove out the multi-agent
document/task conventions by hand: a small Node.js HTTP health-check service, built
by simulated planner/developer/reviewer agents following the doc pyramid and task
JSON contract that later became `club init`'s generated structure and
`schemas/task.schema.json` / `src/clubs/templates/task.schema.json`.

It's kept here as a real, historical example of the workflow the CLI now automates —
see `tasks/`, `logs/comms/`, `logs/reviews/`, `agents/roles/`, and `docs/00-governance/`
through `docs/07-runbooks/` for the original artifacts.

## Core operating principle (as originally written)

Each agent:

1. works in its own Git worktree and branch;
2. owns an explicitly assigned task;
3. edits only files allowed by the task contract;
4. records decisions, tests, inputs, outputs, and changed files;
5. opens a pull request;
6. never merges its own work unless explicitly authorized.

The repository is the shared memory. Git branches isolate implementation. Structured
task files coordinate ownership. (`club` now does the branch/worktree/PR-draft part
of this automatically — see `docs/cli/workflow.md`.)

## Recommended local setup (manual, pre-CLI)

```bash
git clone <repository-url>
cd <repository>

git worktree add ../project-agent-architect -b agent/architect/main
git worktree add ../project-agent-backend -b agent/backend/main
git worktree add ../project-agent-reviewer -b agent/reviewer/main
```

Run one agent in each terminal and worktree.

## Local HTTP service

This repository includes a dependency-free Node.js HTTP service, built as the
example project.

Run it locally:

```bash
node src/server/server.mjs
```

Optional configuration:

```bash
HOST=127.0.0.1 PORT=3000 node src/server/server.mjs
```

Use `PORT=0` to bind an ephemeral local port for smoke tests.

Public contract:

| Method | Path | Response |
|---|---|---|
| `GET` | `/` | `200` service metadata |
| `HEAD` | `/` | `200` headers only, no body |
| `OPTIONS` | `/` | `204`, `Allow: GET, HEAD, OPTIONS` |
| `GET` | `/health` | `200`, `{ "status": "ok" }` |
| `HEAD` | `/health` | `200` headers only, no body |
| `OPTIONS` | `/health` | `204`, `Allow: GET, HEAD, OPTIONS` |
| unsupported method | `/` or `/health` | `405` JSON `method_not_allowed` |
| any method | unknown path | `404` JSON `not_found` |

Run tests:

```bash
node --test tests/health/health.test.mjs tests/server/server.test.mjs
```

Final local verification is recorded in `logs/tests/TASK-022.md` and
`docs/06-handoffs/TASK-022.md`.

## Original main documents

- `MASTER_CONTRACT.md` — project constitution and non-negotiable rules.
- `docs/01-product/PRODUCT_OVERVIEW.md` — what is being built and why.
- `docs/02-architecture/SYSTEM_ARCHITECTURE.md` — high-level technical design.
- `docs/03-delivery/AGENT_OPERATING_MODEL.md` — how agents coordinate and deliver.
- `docs/00-governance/DEVELOPMENT_STANDARD.md` — implementation rules.
- `docs/00-governance/AUDIT_STANDARD.md` — audit requirements.
- `docs/00-governance/TEST_STANDARD.md` — test evidence requirements.
- `docs/03-delivery/CI_CD_STANDARD.md` — CI/CD policy.

## Task lifecycle (original, manual)

```text
backlog -> active -> review -> done
```

A task moves between directories. The task JSON is the source of truth for status,
ownership, scope, dependencies, and evidence — the same shape `club task` now reads
and writes automatically.

## Golden rule

No agent starts implementation without an assigned task JSON containing:

- one owner;
- allowed files or directories;
- acceptance criteria;
- dependencies;
- required tests;
- expected output.
