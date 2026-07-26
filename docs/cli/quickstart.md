# Quickstart

This walks through one full task lifecycle, using the default `dummy` provider (no
API keys, no real code generation — it proves the mechanics, not the coding).

## 1. Initialize a club

```bash
cd your-project   # ideally a git repo, so Git worktree isolation works (see workflow.md)
club init
```

The wizard asks for:

1. **Club name** — defaults to the current directory name.
2. **Project type** — an arrow-key picker; only "Software development" exists in this
   version, so it's really just a confirm-and-continue.
3. **Repository root** / **Main branch**.
4. **Collaboration pattern** — an arrow-key picker over the 5 patterns (see
   [patterns.md](patterns.md)); non-interactive/piped input falls back to a numbered
   prompt.
5. Pattern-specific follow-ups (role names, worker count, component names, or custom
   role/capability picks — depends on the pattern chosen).
6. **Master Contract location** — where the project constitution document lives.

On success it generates `.clubs/club.yaml`, the document pyramid, `tasks/`, `logs/`,
and the runtime folders — then (in a real terminal) plays a short ASCII intro.

## 2. Check it

```bash
club validate   # config/docs/folders all present and well-formed
club status     # agents (all "offline" until started), task counts, missions
```

## 3. Create a mission and a task

```bash
club mission create
# Mission title: Add greet()
# Description: Add a greet(name) function with tests.
# Priority: (arrow-key pick, defaults to medium)
# -> Mission 'MISSION-001' created.

club task create
# Mission: (pick MISSION-001)
# Task title: Add greet()
# Objective: Add a greet(name) function with tests.
# Priority: medium
# -> Task 'TASK-001' created in backlog.
```

## 4. Run the lifecycle

Each configured role needs a tick. In separate terminals (this is the "one shell per
agent" model — see the master design brief's core principles):

```bash
club agent start planner       # decomposes any pending mission into a task (already done above)
club agent start coordinator   # assigns backlog tasks to a free, capable agent
club agent start developer     # "implements" (marks acceptance criteria verified; commits
                                #  NOTES.md in its isolated worktree if one exists)
club agent start reviewer      # approves
club agent start coordinator   # merges (moves the task to done)
```

Each command loops until Ctrl+C, polling on `runtime.polling_interval_seconds`
(default 3s). Stop each one once you see its job is done — `club status` shows task
counts moving through backlog → active → review → done in real time from another
terminal.

## 5. Inspect what happened

```bash
club task list                 # every task, every stage
club task show TASK-001         # full task JSON: owner, acceptance criteria, audit trail
```

If your project root is a real Git repository, `task["owner"]["worktree"]` points at a
real sibling directory (`../<repo>-developer-TASK-001`) with a real branch and a real
commit — see [workflow.md](workflow.md) for exactly what Milestone 9's Git isolation
does and why.

## Next steps

- Swap the pattern: re-run `club init` in a fresh directory and pick `Master -> Workers`
  or `Custom` — see [patterns.md](patterns.md).
- Try a real provider instead of the dummy one — see [providers.md](providers.md), and
  read its safety section before you do.
