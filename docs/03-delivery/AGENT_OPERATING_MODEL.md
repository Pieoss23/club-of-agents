# Agent Operating Model

## Objective

Enable multiple AI agents to work concurrently while sharing context and avoiding duplicated or conflicting changes.

## Recommended model: bounded supervisor-worker

The default pattern combines:

- a Project Master that plans and delegates;
- bounded Worker Agents that implement isolated tasks;
- independent Reviewer Agents;
- specialist agents called only when their expertise is needed;
- Git as the integration and audit layer.

## Supported collaboration patterns

### 1. Role branches

Each agent permanently represents a domain:

- product;
- architecture;
- frontend;
- backend;
- database;
- test;
- security;
- DevOps.

Best for stable ownership and long-running projects.

Risk: role branches become stale or too broad.

### 2. Master delegation

One Project Master decomposes work into small task contracts and assigns temporary workers.

Best for coordinated delivery and dependency management.

Risk: the Project Master becomes a bottleneck.

### 3. Blackboard pattern

Agents read and write structured facts, decisions, blockers, and tasks to a shared repository area. Agents do not communicate only through chat; the shared state is durable.

Recommended shared artifacts:

- task JSON;
- ADRs;
- handoffs;
- audit logs;
- ownership registry;
- dependency graph.

Best for asynchronous work and recovery after context loss.

### 4. Contract-net pattern

The Project Master publishes a task. Specialist agents propose an approach, estimated impact, risks, and files needed. The master awards the task to one agent.

Best when the correct specialist is not obvious.

### 5. Pipeline pattern

Work passes through explicit stages:

```text
analysis -> design -> implementation -> test -> security review -> integration
```

Each stage has a different owner.

Best for regulated, risky, or complex features.

### 6. Pair-agent pattern

One agent implements while another continuously reviews tests, assumptions, and diffs.

Best for fragile code, migrations, authentication, and security-sensitive work.

### 7. Swarm with bounded territories

Many agents work simultaneously, but each receives a non-overlapping path or component boundary.

Best for broad refactors with mechanically separable work.

Risk: integration problems if interfaces are not frozen first.

## Recommended hybrid

Use:

- master delegation for planning;
- blackboard for persistent shared context;
- worktrees for isolation;
- pipeline reviews for medium/high risk;
- pair-agent review for critical code;
- contract-net only for ambiguous specialist work.

## Agent startup protocol

Every agent must:

1. declare identity and role;
2. read the master contract;
3. read its role document;
4. load the assigned task;
5. inspect dependencies and active tasks;
6. confirm allowed paths;
7. update its branch from the integration branch;
8. write a start entry in the task;
9. begin work.

## Agent completion protocol

Every agent must:

1. update implementation;
2. update documentation;
3. run tests;
4. record test evidence;
5. create an audit entry;
6. create a handoff;
7. update the task to `review`;
8. open a pull request;
9. stop editing the task scope unless review requests changes.
