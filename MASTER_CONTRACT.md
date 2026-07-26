# Master Project Contract

## 1. Purpose

This document is the highest-level contract for humans and AI agents contributing to this repository.

It defines:

- project authority;
- shared context rules;
- ownership;
- task delegation;
- branch isolation;
- change control;
- review requirements;
- testing;
- auditability;
- conflict prevention.

If another document conflicts with this contract, this contract wins.

## 2. Sources of truth

The repository contains several kinds of truth:

1. `MASTER_CONTRACT.md`: governance and non-negotiable rules.
2. `docs/01-product/`: product intent, scope, terminology, and requirements.
3. `docs/02-architecture/`: architecture and technical boundaries.
4. `docs/05-decisions/`: accepted Architecture Decision Records.
5. `tasks/`: current operational work and ownership.
6. source code: current executable implementation.
7. tests and CI results: evidence that implementation behaves as expected.

Agents must not silently reinterpret these sources.

## 3. Authority model

### Project Master

The Project Master:

- decomposes goals into tasks;
- assigns owners;
- resolves ambiguity;
- approves scope changes;
- coordinates dependencies;
- decides whether work is accepted, revised, or rejected;
- can delegate review but remains accountable for integration.

### Worker Agent

A Worker Agent:

- accepts one bounded task;
- works only inside the assigned scope;
- records assumptions;
- implements changes;
- runs required tests;
- produces a handoff;
- requests review.

### Reviewer Agent

A Reviewer Agent:

- does not author the implementation under review;
- verifies acceptance criteria;
- checks regressions, security, architecture, and documentation;
- records findings;
- approves or requests changes.

### Specialist Agent

A Specialist Agent provides analysis in a defined domain such as security, database, UX, testing, or performance. It may produce recommendations without modifying implementation unless assigned a separate implementation task.

## 4. Isolation rules

Each active agent must use:

- a separate terminal;
- a separate Git worktree;
- a separate branch;
- one declared agent identity;
- one active task at a time unless the task explicitly allows subtasks.

Branch naming:

```text
agent/<role>/<task-id>-<short-slug>
```

Example:

```text
agent/backend/TASK-004-create-user-api
```

Agents must not develop directly on `main`.

## 5. File ownership

Every task must define one of:

- `allowed_paths`;
- `owned_components`;
- `exclusive_files`.

An agent must not edit outside the declared scope unless:

1. it identifies the need;
2. updates the task or creates a dependency task;
3. receives approval from the Project Master.

Shared high-conflict files should have an explicit temporary owner.

Examples:

- dependency lockfiles;
- root configuration;
- database migrations;
- API schemas;
- central routing;
- global styles;
- CI workflows.

## 6. Task contract

No implementation starts without a task JSON.

A valid task contains:

- unique ID;
- title;
- objective;
- owner;
- status;
- scope;
- allowed paths;
- forbidden paths;
- dependencies;
- acceptance criteria;
- tests;
- expected artifacts;
- risk level;
- audit requirements.

The assigned agent must update the task as work progresses.

## 7. Change rules

Every insert, update, rename, move, or deletion must be traceable.

For each change, record:

- why the change is needed;
- files affected;
- behavior before;
- behavior after;
- migration or compatibility impact;
- tests run;
- unresolved risks.

Destructive changes require explicit review.

## 8. Documentation rules

Documentation must be updated in the same pull request when behavior, API, architecture, configuration, deployment, or operational procedures change.

Feature documentation must describe:

- purpose;
- user or system behavior;
- interfaces;
- data;
- edge cases;
- failure modes;
- security considerations;
- observability;
- tests;
- open questions.

## 9. Testing rules

An agent must never claim success without evidence.

At minimum, report:

- command executed;
- environment;
- input;
- expected output;
- actual output;
- result;
- relevant logs.

A failing test may be documented, but it must not be represented as passing.

## 10. Pull request rules

Every implementation must be delivered through a pull request containing:

- task ID;
- summary;
- changed files;
- design decisions;
- tests and results;
- risks;
- rollback notes;
- screenshots or logs when useful;
- linked task JSON;
- linked ADRs.

The author cannot be the final reviewer for medium- or high-risk changes.

## 11. Merge rules

A change may merge only when:

- acceptance criteria are satisfied;
- required CI checks pass;
- required review is complete;
- documentation is updated;
- task status is `review`;
- no unresolved blocking finding exists.

After merge:

- task moves to `done`;
- final commit and PR references are recorded;
- relevant context documents are updated;
- obsolete temporary notes are archived or removed.

## 12. Conflict prevention

Before editing, each agent must:

1. read the task;
2. check dependencies;
3. inspect active tasks;
4. confirm path ownership;
5. rebase or update from the integration branch;
6. announce ownership in the task file.

If two tasks overlap, implementation pauses until the Project Master resolves ownership.

## 13. Context management

Agents should read context in this order:

1. `MASTER_CONTRACT.md`;
2. assigned role;
3. assigned task JSON;
4. relevant macro document;
5. relevant feature document;
6. relevant ADRs;
7. related code and tests;
8. recent handoffs and audit entries.

Agents should not ingest the entire repository when narrower context is sufficient.

## 14. Definition of done

A task is done only when:

- implementation is complete;
- acceptance criteria are verified;
- tests pass or approved exceptions are documented;
- audit entry exists;
- handoff exists;
- documentation is current;
- review is approved;
- PR is merged;
- task JSON is finalized.
