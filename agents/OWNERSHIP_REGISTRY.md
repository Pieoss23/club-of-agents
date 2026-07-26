# Ownership Registry

Temporary ownership is recorded here for high-conflict paths.

| Path or component | Owner agent | Task | Start | Expected release | Status |
|---|---|---|---|---|---|
| Example: package-lock.json | agent-backend-01 | TASK-001 | YYYY-MM-DD | YYYY-MM-DD | active |

Rules:

- one active owner per exclusive path;
- ownership ends after merge or explicit release;
- stale ownership must be resolved by the Project Master;
- this registry does not replace task-level `allowed_paths`.
