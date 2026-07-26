# Context Map

## Purpose

Prevent agents from reading too much irrelevant context while ensuring they load all required information.

## Reading map

| Task type | Required context |
|---|---|
| Product requirement | Master contract, product overview, relevant feature docs |
| Architecture | Master contract, product overview, system architecture, related ADRs |
| Implementation | Master contract, role, task JSON, feature doc, relevant ADRs, code/tests |
| Database | Master contract, task, architecture, data docs, migration standard |
| Review | Master contract, task, feature doc, diff, tests, audit, handoff |
| CI/CD | Master contract, delivery docs, CI/CD standard, deployment runbooks |
| Security | Master contract, task, architecture, feature security section, threat model |

## Context freshness

An agent must prefer:

1. accepted ADRs over old discussion;
2. active task JSON over chat messages;
3. merged documentation over branch-local notes;
4. current code and tests over stale summaries.

Context contradictions must be reported, not silently resolved.
