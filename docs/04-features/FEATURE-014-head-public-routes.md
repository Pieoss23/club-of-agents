# FEATURE-014 — HEAD Support for Public Routes

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Allow clients and monitors to check public route availability with `HEAD` requests without downloading response bodies.

## Scope

### Included

- `HEAD /` returns HTTP `200` with the same JSON headers as `GET /` and no body
- `HEAD /health` returns HTTP `200` with the same JSON headers as `GET /health` and no body
- Unsupported methods on `/` and `/health` return `405` with `Allow: GET, HEAD`
- Existing `GET`, `404`, logging, configuration, CLI startup, and shutdown behavior remains passing

### Excluded

- CORS preflight policy
- HEAD support for unknown paths beyond existing fallback behavior
- Additional public routes

## Interface

```http
HEAD /
HEAD /health
```

Successful `HEAD` responses include JSON content headers and content length, but no response body.

Unsupported methods on known public routes return:

```http
HTTP/1.1 405 Method Not Allowed
Allow: GET, HEAD
Content-Type: application/json; charset=utf-8
```

```json
{ "error": "method_not_allowed", "allowed": ["GET", "HEAD"] }
```

## Security considerations

- No request body, query string, secrets, or environment variables are returned.
- `HEAD` responses intentionally omit bodies while preserving status and headers for availability checks.

## Acceptance criteria

- [x] AC-1: `HEAD /` returns HTTP 200 and no response body.
- [x] AC-2: `HEAD /health` returns HTTP 200 and no response body.
- [x] AC-3: Unsupported methods on `/` and `/health` return 405 with `Allow: GET, HEAD` and existing behavior remains passing.

## Test plan

- integration: verify `HEAD /` status, content type, and empty body
- integration: verify `HEAD /health` status, content type, and empty body
- regression: verify unsupported methods return `405` with `Allow: GET, HEAD`
- regression: full health and server test suite

## Dependencies

- tasks: `TASK-012`
- components: `src/health/health.mjs`, `src/server/server.mjs`
- external systems: none
