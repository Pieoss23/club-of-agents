# FEATURE-001 — Health Check

## Status

Implemented

## Owner

Implementer agent `019f9954-0bf4-7d10-94a8-56ef18c92649`

## Purpose

Provide a lightweight process-availability endpoint for operators, load balancers, and deployment automation.

## Scope

### Included

- `GET /health`
- HTTP 200 response when the process can serve requests
- Stable JSON body: `{ "status": "ok" }`

### Excluded

- Database, dependency, or downstream service checks
- Authentication-specific behavior
- Readiness or liveness split

## Interfaces

HTTP:

```http
GET /health
```

Success response:

```http
HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Cache-Control: no-store
```

```json
{ "status": "ok" }
```

## Data

The response contains one documented field:

| Field | Type | Value | Description |
|---|---|---|---|
| `status` | string | `ok` | Process can serve the health endpoint. |

No persistent data, sensitive data, or migrations are introduced.

## Failure modes

| Failure | Detection | Behavior | Recovery |
|---|---|---|---|
| Process unavailable | Connection failure or timeout | No HTTP response | Restart or roll back the process |
| Wrong route or method | Non-`GET /health` request | Handler declines the request | Upstream application returns its normal response |

## Security considerations

- authentication: none required by this endpoint contract
- authorization: no sensitive data is exposed
- validation: method and path are explicitly checked
- sensitive data: response contains no secrets, configuration, or dependency status
- abuse cases: response is constant and lightweight
- audit events: none required for health polling

## Observability

- Health state is externally observable through HTTP status and JSON body.
- Response uses `Cache-Control: no-store` to avoid stale health signals.

## Acceptance criteria

- [x] AC-1: `GET /health` returns HTTP 200 when the process is healthy.
- [x] AC-2: Response contains documented `status` field.

## Test plan

- unit: verify health response contract and route matching
- integration: run an HTTP server and verify `GET /health` status, content type, and JSON body

## Dependencies

- tasks: `TASK-001`
- ADRs: none
- components: API / process health
- external systems: none
