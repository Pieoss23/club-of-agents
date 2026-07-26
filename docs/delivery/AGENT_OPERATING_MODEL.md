# Agent Operating Model — gege

## Default workflow

`mission → planning → implementation → review → integration → done`

The planner prepares tasks, the developer implements them, the reviewer verifies them, and the coordinator integrates approved work.

## Communication

Agents use structured filesystem messages in `.clubs/runtime/`. Important actions must be recorded as durable evidence.
