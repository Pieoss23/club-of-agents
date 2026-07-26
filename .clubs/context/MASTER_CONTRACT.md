# Master Contract — gege

## Authority

This contract is the highest-level agreement for this repository. The repository is the durable source of truth for the club.

## Sources of truth

1. This Master Contract;
2. product, architecture, and delivery documents under `docs/`;
3. task contracts under `tasks/`;
4. executable source code and test evidence.

## Roles and ownership

Each agent has one declared role and one bounded task at a time. No agent may expand task scope or edit outside allowed paths without explicit coordination.

## Quality, review, and integration

Implementation requires explicit acceptance criteria and test evidence. Developers do not approve or merge their own changes. A reviewer records findings; the coordinator authorizes integration only after review.

## Definition of done

A task is done when its accepted implementation, tests, documentation, handoff, and audit evidence are complete and recorded.
