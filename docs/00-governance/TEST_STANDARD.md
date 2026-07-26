# Test Standard

## Test evidence

For each executed test, record:

- task ID;
- agent ID;
- timestamp;
- environment;
- command;
- input or fixture;
- expected output;
- actual output;
- pass/fail status;
- log or artifact path;
- commit hash.

## Test levels

| Level | Purpose | Typical owner |
|---|---|---|
| Unit | Verify isolated logic | Implementer |
| Integration | Verify component collaboration | Implementer/Test agent |
| Contract | Verify interface compatibility | API/Integration agent |
| End-to-end | Verify user workflow | Test agent |
| Security | Verify abuse and controls | Security agent |
| Performance | Verify latency, load, resource use | Performance agent |
| Migration | Verify schema/data transition | Database agent |

## Required behavior

- A bug fix must include a regression test when feasible.
- A new feature must test acceptance criteria.
- A changed API must include contract tests.
- A migration must be tested on representative data.
- Failed tests must be reported exactly.
- Manual tests require reproducible steps.

## Test log location

```text
logs/tests/<task-id>.md
```
