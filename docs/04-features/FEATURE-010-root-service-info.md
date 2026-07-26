# FEATURE-010 — Root Service Information

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Provide a lightweight `GET /` endpoint so humans and simple tooling can discover what the local HTTP service exposes.

## Scope

### Included

- `GET /` JSON service metadata
- Stable list of currently available routes
- No sensitive runtime data in the response
- Regression coverage for existing server behavior

### Excluded

- OpenAPI generation
- Dynamic route discovery
- Environment, host, process, or secret disclosure
- Authentication-specific behavior

## Interface

```http
GET /
```

Success response:

```json
{
  "name": "club-of-agents",
  "status": "available",
  "endpoints": [
    { "method": "GET", "path": "/", "description": "Service information" },
    { "method": "GET", "path": "/health", "description": "Process health check" }
  ]
}
```

## Security considerations

- authentication: none required by this endpoint contract
- authorization: no sensitive data is exposed
- validation: method and path are explicitly checked
- sensitive data: response excludes environment variables, secrets, request bodies, and query strings
- abuse cases: response is constant and lightweight

## Acceptance criteria

- [x] AC-1: `GET /` returns HTTP 200 with JSON service metadata.
- [x] AC-2: The root response lists the health endpoint without exposing secrets, environment variables, or request data.
- [x] AC-3: Existing health, 404, logging, configuration, and shutdown behavior remains passing.

## Test plan

- integration: verify `GET /` status, content type, name, status, endpoint list, and absence of secret/env fields
- regression: verify existing health, JSON 404, logging, configuration, and shutdown tests pass

## Dependencies

- tasks: `TASK-002`, `TASK-003`, `TASK-004`, `TASK-006`
- components: `src/server/server.mjs`
- external systems: none
