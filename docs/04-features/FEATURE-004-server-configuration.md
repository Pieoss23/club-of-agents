# FEATURE-004 — Server Configuration Validation

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Make local HTTP server startup predictable by parsing `HOST` and `PORT` explicitly and failing clearly when the port is invalid.

## Scope

### Included

- Default host: `127.0.0.1`
- Default port: `3000`
- Explicit host override support
- Numeric and numeric-string port override support
- Clear `RangeError` for invalid ports

### Excluded

- Configuration files
- Secret handling
- Production deployment settings
- Package scripts

## Interface

Programmatic configuration parser:

```js
parseServerConfig({ host: '0.0.0.0', port: '8080' });
// { host: '0.0.0.0', port: 8080 }
```

Startup still supports environment variables:

```bash
HOST=0.0.0.0 PORT=8080 node src/server/server.mjs
```

## Validation rules

| Field | Default | Validation |
|---|---|---|
| `host` | `127.0.0.1` | Converted to string |
| `port` | `3000` | Integer from `0` through `65535` |

Invalid ports throw:

```text
RangeError: PORT must be an integer between 0 and 65535
```

## Acceptance criteria

- [x] AC-1: Default server configuration resolves to host `127.0.0.1` and port `3000`.
- [x] AC-2: Valid host and port overrides are accepted.
- [x] AC-3: Invalid port values fail with a clear `RangeError` before server bind.

## Test plan

- unit: verify defaults
- unit: verify explicit host and port overrides
- unit: verify invalid ports throw before bind
- regression: verify health, 404, and request logging behavior still passes

## Dependencies

- tasks: `TASK-002`, `TASK-003`
- components: `src/server/server.mjs`
- external systems: none
