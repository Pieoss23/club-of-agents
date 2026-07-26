# FEATURE-006 — HTTP Server Shutdown

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Provide a small, dependency-free shutdown path for the local HTTP server so tests, scripts, and CLI signal handlers can close the server cleanly.

## Scope

### Included

- Promise-based `stopServer(server)` helper
- Safe no-op behavior when no running server is supplied
- CLI `SIGINT` and `SIGTERM` shutdown handler registration
- Tests for helper and signal handler registration

### Excluded

- Process supervisor integration
- Draining long-running requests beyond Node.js `server.close()` behavior
- Production deployment configuration

## Interfaces

Programmatic shutdown:

```js
const { server } = await startServer();
await stopServer(server);
```

CLI behavior:

```bash
node src/server/server.mjs
```

When started directly, the server registers one-time `SIGINT` and `SIGTERM` handlers. On shutdown success the process exits with code `0`; on shutdown failure it logs the error and exits with code `1`.

## Failure modes

| Failure | Detection | Behavior | Recovery |
|---|---|---|---|
| No server supplied | `stopServer()` receives `undefined` | No-op | None needed |
| Server already stopped | `server.listening` is false | No-op | None needed |
| Close error | `server.close()` callback receives error | Promise rejects; CLI logs and exits `1` | Investigate server state |

## Acceptance criteria

- [x] AC-1: A promise-based helper closes a running HTTP server cleanly.
- [x] AC-2: Calling the helper with no server is a safe no-op.
- [x] AC-3: The CLI entry point installs `SIGINT` and `SIGTERM` shutdown handlers.

## Test plan

- unit: verify no-op shutdown cases
- integration: start a server and close it with `stopServer()`
- unit: verify signal handlers are registered
- regression: verify health, 404, logging, and configuration behavior still passes

## Dependencies

- tasks: `TASK-002`, `TASK-003`, `TASK-004`
- components: `src/server/server.mjs`
- external systems: none
