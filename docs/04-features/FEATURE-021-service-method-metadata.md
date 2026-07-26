# FEATURE-021 — Service Method Metadata

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Keep the root service information response aligned with the HTTP methods currently supported by each public route.

## Scope

### Included

- `GET /` lists `/` with supported methods `GET`, `HEAD`, and `OPTIONS`
- `GET /` lists `/health` with supported methods `GET`, `HEAD`, and `OPTIONS`
- Metadata remains static and non-sensitive
- Full server regression remains passing

### Excluded

- Dynamic route discovery
- OpenAPI generation
- Environment, process, secret, or request data disclosure

## Interface

```http
GET /
```

Success response shape:

```json
{
  "name": "club-of-agents",
  "status": "available",
  "endpoints": [
    {
      "path": "/",
      "methods": ["GET", "HEAD", "OPTIONS"],
      "description": "Service information"
    },
    {
      "path": "/health",
      "methods": ["GET", "HEAD", "OPTIONS"],
      "description": "Process health check"
    }
  ]
}
```

## Security considerations

- Metadata exposes only public route paths, supported methods, and descriptions.
- No request bodies, query strings, environment variables, secrets, process IDs, hostnames, or dependency details are returned.

## Acceptance criteria

- [x] AC-1: `GET /` lists `/` with supported methods `GET`, `HEAD`, `OPTIONS`.
- [x] AC-2: `GET /` lists `/health` with supported methods `GET`, `HEAD`, `OPTIONS`.
- [x] AC-3: Service metadata remains non-sensitive and full regression tests pass.

## Test plan

- integration: verify root endpoint method metadata for `/`
- integration: verify root endpoint method metadata for `/health`
- regression: full health and server test suite

## Dependencies

- tasks: `TASK-017`
- components: `src/server/server.mjs`
- external systems: none
