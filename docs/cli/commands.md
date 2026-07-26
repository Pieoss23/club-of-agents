# Command reference

Every command accepts `--path PATH` (default `.`) to operate on a club rooted
somewhere other than the current directory.

## `club`

No arguments: shows the interactive menu (create/validate/status/list agents/start an
agent/exit). Options 3-6 are wired to the same commands below; option 6 additionally
lets you arrow-key-pick which configured agent to start.

- `club --version` — print the installed version.
- `club --help` — Typer's generated help for every command below.

## `club init [--force]`

Runs the interactive wizard (see [quickstart.md](quickstart.md) for the full prompt
sequence) and generates `.clubs/club.yaml`, the document pyramid, `tasks/`, `logs/`,
and runtime folders.

- Never silently overwrites an existing generated file — if `MASTER_CONTRACT.md` (or
  wherever you pointed the Master Contract) already exists, `init` stops with an error
  listing exactly which file(s) are in the way.
- `--force` explicitly allows overwriting those files. Nothing else is affected.
- Exit code `1` on any validation failure (bad project type, empty club name, empty
  role list, invalid Master Contract path).

## `club validate [--path PATH]`

Checks: `.clubs/club.yaml` exists and parses, the whole config validates against the
Pydantic models, the workflow pattern is one of the 5 known patterns, every role name
is lowercase-alnum-hyphen, every agent's `provider` is one of `dummy/shell/claude/codex`
(and `shell` agents have `provider_command` set), the Master Contract file exists, the
three core documentation files exist, the task schema file exists, and every required
directory exists. Prints a table of checks; exit code `1` if anything failed.

## `club status [--path PATH]`

Prints: club name + workflow pattern, a table of every configured agent (role, agent
id, state — read from `.clubs/runtime/state/<id>.json`, `"offline"` if no state file
exists yet — and current task id), and a table of task counts per stage plus mission
count. Runs `validate_club` first; if the club is invalid, prints a pointer to `club
validate` instead of a stack trace, exit code `1`.

## `club agent list [--path PATH]`

Same agent table as `status`, without the task-count table. Same "invalid club" error
handling.

## `club agent start AGENT_ID [--path PATH] [--provider dummy|shell|claude|codex]`

Runs one agent's poll loop until Ctrl+C: heartbeat, route pending messages, call
whichever of `plan/assign/implement/review/merge` match the agent's configured
capabilities (`can_plan`, `can_assign`, `can_code`, `can_review`, `can_merge` in
`club.yaml`), route messages again, write state, sleep `runtime.polling_interval_seconds`
(default 3s), repeat.

- Provider defaults to whatever `club.yaml` has for that agent (`dummy` unless you set
  it — see [configuration.md](configuration.md)); `--provider` overrides it for this run
  only, without editing the file.
- Starting anything other than `dummy` prints a yellow warning banner before the loop
  begins — see [providers.md](providers.md) for what it actually does and why that
  banner matters.
- Ctrl+C writes `status: offline` for that agent and exits cleanly.
- Unknown agent id → exit code `1` listing the known ids. No club found here → exit
  code `1` pointing at `club init`.

## `club mission create [--path PATH]`

## `club agent ping TO_AGENT --from FROM_AGENT [--timeout SECONDS] [--message TEXT]`

Verifies the filesystem message bus across **two running agent shells** without
calling an AI provider. Start both agents in separate terminals, then run the test
from a third terminal:

```bash
club agent start planner
club agent start developer
club agent ping developer --from planner --timeout 15 --message "can you hear me?"
```

The running `developer` shell consumes the ping and sends a pong. The running
`planner` shell consumes the reply; the command then confirms `direct communication
verified`. The shared event log records the sent, received, reply-sent and
reply-received events with the correlation id. A timeout normally means one of the
two agent shells is not running, uses a different club root, or is polling too
slowly; increase `--timeout` if needed.

Interactive: title, description, priority (arrow-key pick over
low/medium/high/critical). Writes `.clubs/missions/MISSION-{n:03d}.json`
(sequential, zero-padded). Exit code `1` on an invalid club or invalid priority.

## `club task create [--path PATH]`

Interactive: pick an existing mission (arrow-key pick — fails with a clear message if
there are no missions yet), title, objective, priority. Writes
`tasks/backlog/TASK-{n:03d}.json` validated against the bundled task schema, and
appends the new task id to that mission's `tasks` list. Exit code `1` if task creation
fails schema validation or the club is invalid.

## `club task list [--stage backlog|active|review|blocked|done] [--path PATH]`

Table of every task (id, stage, title, status, owner) across all 5 stage directories,
or just one with `--stage`. Invalid stage name → exit code `1` listing the valid ones.

## `club task show TASK_ID [--path PATH]`

Finds the task by id in whichever stage directory currently holds it and pretty-prints
its full JSON (owner, acceptance criteria, audit trail including `commits` and
`pull_request` once Git isolation has run — see [workflow.md](workflow.md)). Unknown id
→ exit code `1`.

## `club task cleanup [--path PATH] [--yes]`

Scans `tasks/done/*.json` for tasks that still have a real worktree on disk, prints a
table (task id, branch, worktree path), and — unless `--yes` — asks for confirmation
before removing each worktree directory and deleting its branch (`git worktree remove
--force` + `git branch -D`, see [workflow.md](workflow.md#manually-cleaning-up-worktrees)).
Nothing to clean up just prints a message and exits `0`. A failure on one task (e.g. the
branch was already deleted by hand) is reported and skipped, not fatal to the rest.
