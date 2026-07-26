# E2E-CLUB-001 — Workflow acceptance test

## Scope

Validate the safe, documented `club` lifecycle using the built-in `dummy` provider:
initialization, validation, mission creation, task decomposition, assignment, Git
worktree isolation, implementation, review, integration, status, and task inspection.
No real provider (`shell`, `claude`, or `codex`) is invoked.

## Reproducible procedure

| Field | Value |
|---|---|
| Test level | End-to-end / acceptance |
| Agent | Codex test agent |
| Environment | Python 3.12+, local temporary Git repository |
| Automated test | `tests/clubs/test_club_e2e.py::test_documented_dummy_workflow_completes_with_git_audit_artifacts` |
| Command | `python -m pytest tests/clubs/test_club_e2e.py -q` |
| Fixture | Fresh Git repository on branch `main`; interactive `club init` inputs for the planner/developer/reviewer/coordinator pattern |
| Expected result | `TASK-001` reaches `done`, is approved and auditable, has an isolated worktree commit and a local PR draft; lifecycle events are emitted |
| Artifacts checked | `tasks/done/TASK-001.json`, worktree `NOTES.md`, `docs/handoffs/TASK-001-pr-draft.md`, `.clubs/runtime/events/events.jsonl` |
| Commit | Not committed (working tree deliberately preserved) |

## Acceptance assertions

1. `club init` succeeds and `club validate` reports a valid club.
2. `club mission create` creates `MISSION-001`.
3. Planner, coordinator, developer, reviewer, coordinator ticks transition one task
   through `backlog -> active -> review -> done`.
4. A real Git worktree and branch are created; the dummy implementation creates a
   commit and integration produces a local PR draft.
5. `club status`, `club task list --stage done`, and `club task show TASK-001` expose
   the completed task.
6. The event log contains the creation, assignment, review, and completion trail.

## Execution result

| Timestamp | 2026-07-26 (Europe/Rome) |
|---|---|
| Actual output | `1 passed` |
| Status | PASS |
| Failure details | None |

The isolated test completed in 3.7 seconds. The current repository commit is
`ff915b6`; the test and this log remain uncommitted alongside pre-existing local
