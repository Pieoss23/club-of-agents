# FEATURE-012 — Method Not Allowed Responses

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Return explicit HTTP `405 Method Not Allowed` responses when clients use unsupported methods on known routes.

## Scope

### Included

- `POST /` and other non-`GET` methods on `/` return JSON `405`
- `POST /health` and other non-`GET` methods on `/health` return JSON `405`
- `Allow: GET` response header for known routes
- Unknown paths continue to return JSON `404`

### Excluded

- CORS preflight policy
- Authentication-specific behavior
- Route methods other than existing `GET` support

## Interface

Unsupported method response for known routes:

```http
HTTP/1.1 405 Method Not Allowed
Allow: GET
Content-Type: application/json; charset=utf-8
```

```json
{ "error": "method_not_allowed", "allowed": ["GET"] }
```

Unknown path response remains:

```json
{ "error": "not_found" }
```

## Security considerations

- Response discloses only allowed method metadata for already-public routes.
- No request body, query string, environment variable, or secret is returned.

## Acceptance criteria

- [x] AC-1: Unsupported methods on `/` return HTTP 405 JSON response with `Allow: GET`.
- [x] AC-2: Unsupported methods on `/health` return HTTP 405 JSON response with `Allow: GET`.
- [x] AC-3: Unknown paths still return JSON 404 and existing behavior remains passing.

## Test plan

- integration: `POST /` returns `405` and JSON method error
- integration: `POST /health` returns `405` and JSON method error
- regression: unknown paths return `404`
- regression: full health and server tests pass

## Dependencies

- tasks: `TASK-010`, `TASK-011`
- components: `src/server/server.mjs`
- external systems: none
