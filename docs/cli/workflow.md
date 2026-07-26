# Task lifecycle, Git isolation, and path policy

This is what actually happens to a task between `club task create` and `done` — the
mechanics live in `src/clubs/workflow.py`, `git_ops.py`, and `path_policy.py`, all
provider-agnostic (a `DummyProvider` and a real `ClaudeProvider` go through exactly
the same code here — see [providers.md](providers.md) and [architecture.md](architecture.md)).

## Stages

```text
backlog -> active -> review -> done
             ^          |
             (blocked exists as a stage directory, not yet wired into any transition)
```

A task is a JSON file that *moves between directories* — the directory it's in **is**
its status. `tasks.move_task` renames the file; if the source is already gone
(another process claimed it first), it returns `None` instead of raising — every
transition below is written to be race-safe on that basis.

## The four transitions

### `assign_task` (backlog → active)

Called by whichever agent has `can_assign: true` (`eligible_assignee` picks the first
configured agent with the matching capability — `can_code` by default — that has no
`current_task_id` in its state file). Then:

1. Moves the task file to `tasks/active/`.
2. **Attempts Git isolation**: `git_ops.create_worktree(...)` creates a sibling
   directory `../<repo-name>-<role>-<task-id>` on a new branch
   `agent/<role>/<task-id>-<slugified-title>`, based off `origin/<main_branch>` if a
   remote exists (best-effort `fetch` first) or the local `main_branch` otherwise.
3. **On success**: `task.owner.branch`/`task.owner.worktree` get the real branch/path.
   **On any failure** (not a git repo, git not installed, worktree add failed for any
   reason): falls back to the placeholder `branch: "unavailable-not-a-git-worktree"`,
   `worktree: <repo root>` — the assignment still succeeds, it's just not isolated.
   This is why the whole test suite runs green with or without a real git repo; only
   the tests using the `git_repo` fixture exercise the real-isolation path.

### `submit_for_review` (active → review)

Called after `implement()` does its work (real or simulated). If the task has a
*real* worktree (not the placeholder):

1. `git_ops.commit_all(worktree, "<task-id>: <title>")` — commits everything staged;
   if there's a commit, its sha is appended to `task.audit.commits`.
2. `git_ops.changed_paths(worktree, main_branch)` + `path_policy.check(...)` against
   `task.allowed_paths`/`task.forbidden_paths` (fnmatch patterns). **Warn-only by
   design**: violations get appended to `task.notes` and an event is emitted — the
   transition is never blocked. (A forbidden-path match always wins over an
   allowed-path match, even if a path happens to match both.)

### `approve_review` (stays in review, sets a flag)

Sets `task.review_approved = True` in place — doesn't move the file.

### `reject_review` (review → active, same owner)

A real reviewer provider that decides `approved: false` (see [providers.md](providers.md))
calls this instead: sets `task.review_approved = False`, records the findings in
`task.notes`, and moves the file back to `tasks/active/` — **for the same owner**, not
a reassignment (their branch/worktree already exists). Explicitly refreshes the
owner's `runtime` state to `assigned`/this task id, so the coordinator's
`eligible_assignee` check doesn't double-book them with a different backlog task
before their next tick naturally picks this one back up via
`find_task("active", owner=...)`. The next `implement()` call sees the rejection
findings — `adapters.prompts.implement_prompt` includes `task.notes` — so a real
provider knows what to fix on rework. `DummyProvider` never rejects (it has no real
judgment, it always approves).

### `integrate` (review → done)

Only runs once `review_approved` is true. If the task has a real worktree, writes a
**local PR draft** first — `docs/handoffs/{task-id}-pr-draft.md` (title, objective,
an acceptance-criteria checklist, and the `branch -> main_branch` line) — and records
its path in `task.audit.pull_request`. No network call, nothing pushed; this is
"pull request preparation," not creation (the master design brief's core principle:
the core stays independent of GitHub). Then moves the file to `tasks/done/` and sets
`task.status = "done"` + `task.audit.completed_at`.

## Everything is auditable

- `task.audit.commits` — every real commit sha made in that task's worktree.
- `task.audit.pull_request` — the PR draft's path, once integrated.
- `task.notes` — free-text trail: who implemented, path-policy warnings, review
  findings.
- `.clubs/runtime/events/events.jsonl` — one line per lifecycle event
  (`task.created`, `task.assigned`, `worktree.created`/`worktree.unavailable`,
  `path_policy.violation`, `task.ready_for_review`, `review.approved`,
  `review.rejected`, `task.completed`, `provider.failed`, ...).
- `logs/agents/<agent-id>/<task-id>-<capability>.log` — full prompt + stdout/stderr
  for every real-provider call (see [providers.md](providers.md)).

## Cleaning up worktrees

`club` never removes a worktree automatically. Once a task is `done`, run:

```bash
club task cleanup          # prompts for confirmation, lists what it would remove
club task cleanup --yes    # skips the confirmation (e.g. in a script)
```

which finds every `done` task with a real worktree still on disk and runs
`git_ops.remove_worktree` (`git worktree remove --force`) + `git_ops.delete_branch`
(`git branch -D`) for each — see [commands.md](commands.md#club-task-cleanup---path-path---yes).
`--force` means this deletes uncommitted changes too, which is why confirmation is
required by default.
