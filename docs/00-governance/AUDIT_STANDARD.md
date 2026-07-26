# Audit Standard

## Objective

Every meaningful repository change must be reconstructable.

## Required audit events

- task started;
- ownership changed;
- scope changed;
- file inserted;
- file modified;
- file moved or renamed;
- file deleted;
- dependency changed;
- migration added;
- test executed;
- review finding created;
- task accepted or rejected;
- rollback performed.

## Audit entry format

Store entries in `logs/audit/YYYY-MM-DD.md`.

```markdown
## <timestamp> — <task-id> — <agent-id>

- Action:
- Reason:
- Files:
- Before:
- After:
- Inputs:
- Outputs:
- Tests:
- Risks:
- Commit:
- Pull request:
```

## Audit quality rules

Audit entries must be:

- factual;
- concise;
- append-only;
- linked to evidence;
- free from invented results;
- explicit about failures and uncertainty.

Audit logs should not contain secrets or sensitive payloads.
