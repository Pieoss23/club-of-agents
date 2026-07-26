# FEATURE-002 — Minimal HTTP Server

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Provide a minimal Node.js HTTP server so the repository can serve the implemented health endpoint locally without adding third-party dependencies.

## Scope

### Included

- Node.js server factory
- Local server startup helper
- Mounting of `GET /health`
- JSON `404` response for unknown routes

### Excluded

- Production process manager
- TLS termination
- Authentication and authorization
- Dependency, database, or external service routes

## Interfaces

Start locally:

```bash
node src/server/server.mjs
```

Optional environment variables:

| Variable | Default | Description |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address |
| `PORT` | `3000` | Bind port |

Health request:

```http
GET /health
```

Unknown route response:

```json
{ "error": "not_found" }
```

## Non-functional requirements

- performance: constant lightweight responses
- availability: starts with built-in Node.js modules only
- security: no sensitive data in responses
- observability: startup logs listening URL to stdout
- compatibility: Node.js ES modules

## Acceptance criteria

- [x] AC-1: The server can be started locally with Node.js without extra dependencies.
- [x] AC-2: The server exposes `GET /health` through the existing health handler.
- [x] AC-3: Unknown routes return JSON 404.

## Test plan

- integration: start server on an ephemeral local port and call `GET /health`
- integration: call an unknown route and verify JSON 404

## Dependencies

- tasks: `TASK-001`
- components: `src/health/health.mjs`
- external systems: none
