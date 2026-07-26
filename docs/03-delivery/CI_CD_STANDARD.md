# CI/CD Standard

## Pull request pipeline

Every pull request should run:

1. repository validation;
2. task JSON validation;
3. formatting;
4. linting;
5. type checking;
6. unit tests;
7. integration tests where applicable;
8. dependency and secret scanning;
9. build;
10. documentation link checks;
11. policy checks for protected paths.

## Branch policy

- `main` is protected.
- Direct pushes to `main` are forbidden.
- Required checks must pass.
- At least one independent approval is required.
- High-risk changes require specialist review.
- Force pushes on shared branches are forbidden.

## Environments

Recommended progression:

```text
local -> CI preview -> staging -> production
```

Each environment should define:

- configuration source;
- secrets provider;
- deployment identity;
- rollback mechanism;
- data policy;
- observability;
- approval rules.

## Deployment strategy

Choose per service:

- rolling;
- blue/green;
- canary;
- immutable replacement.

The selected strategy must be documented in the relevant runbook.

## Rollback

Every deployable change must answer:

- what can be rolled back;
- how rollback is triggered;
- whether data is backward compatible;
- how long rollback is safe;
- how success is verified.

## Release evidence

A release record should contain:

- commit;
- included task IDs;
- build identifier;
- environment;
- migration status;
- test summary;
- deployment result;
- rollback status;
- operator.
