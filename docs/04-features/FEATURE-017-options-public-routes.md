# FEATURE-017 — OPTIONS Support for Public Routes

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Allow clients to discover supported HTTP methods for public routes without downloading response bodies.

## Scope

### Included

- `OPTIONS /` returns HTTP `204` with `Allow: GET, HEAD, OPTIONS`
- `OPTIONS /health` returns HTTP `204` with `Allow: GET, HEAD, OPTIONS`
- Unsupported methods on `/` and `/health` return HTTP `405` with the same `Allow` value
- Existing `GET`, `HEAD`, `404`, logging, configuration, CLI startup, and shutdown behavior remains passing

### Excluded

- CORS policy headers
- Authentication-specific behavior
- OPTIONS support for unknown paths

## Interface

```http
OPTIONS /
OPTIONS /health
```

Success response:

```http
HTTP/1.1 204 No Content
Allow: GET, HEAD, OPTIONS
Cache-Control: no-store
Content-Length: 0
```

Unsupported method response for known routes:

```json
{ "error": "method_not_allowed", "allowed": ["GET", "HEAD", "OPTIONS"] }
```

## Acceptance criteria

- [x] AC-1: `OPTIONS /` returns HTTP 204 with `Allow: GET, HEAD, OPTIONS` and no body.
- [x] AC-2: `OPTIONS /health` returns HTTP 204 with `Allow: GET, HEAD, OPTIONS` and no body.
- [x] AC-3: Unsupported methods on `/` and `/health` return 405 with `Allow: GET, HEAD, OPTIONS` and existing behavior remains passing.

## Test plan

- integration: verify `OPTIONS /` status, `Allow` header, and empty body
- integration: verify `OPTIONS /health` status, `Allow` header, and empty body
- regression: verify unsupported methods return `405` with updated allowed methods
- regression: full health and server test suite

## Dependencies

- tasks: `TASK-014`
- components: `src/server/server.mjs`
- external systems: none
