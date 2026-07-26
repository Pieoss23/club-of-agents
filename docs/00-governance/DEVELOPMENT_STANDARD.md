# Development Standard

## General rules

- Make the smallest coherent change.
- Avoid unrelated refactors.
- Prefer explicit interfaces.
- Keep business rules testable without infrastructure.
- Do not hide failures.
- Do not commit secrets, generated credentials, or private data.
- Pin or lock dependencies.
- Maintain backward compatibility unless the task explicitly changes it.

## Before coding

Record:

- objective;
- assumptions;
- dependencies;
- affected components;
- risk;
- rollback strategy.

## During coding

- keep commits focused;
- reference the task ID in commits;
- add tests with behavior changes;
- update documentation;
- preserve style and lint rules;
- avoid editing files outside task scope.

## Commit format

```text
<type>(<scope>): <summary> [TASK-ID]
```

Types:

- `feat`
- `fix`
- `refactor`
- `test`
- `docs`
- `build`
- `ci`
- `chore`
- `security`

## Deletions

Before deleting code, data, configuration, or documentation:

1. search for references;
2. identify dependent behavior;
3. document why deletion is safe;
4. add migration or rollback notes;
5. obtain review for destructive changes.

## Database changes

Database changes require:

- forward migration;
- rollback or documented irreversibility;
- compatibility strategy;
- test data;
- expected duration;
- locking or downtime analysis;
- backup considerations.

## Dependency changes

Record:

- old and new version;
- reason;
- security impact;
- breaking changes;
- lockfile changes;
- verification performed.
