# Test Log — TASK-022

## 2026-07-25T14:40:00Z — Final automated regression

- task ID: TASK-022
- agent ID: 019f9954-0bf4-7d10-94a8-56ef18c92649
- environment: Windows/Git Bash path `/c/dev/pi/club-of-agents`, Node.js v24.13.1
- command: `node --test tests/health/health.test.mjs tests/server/server.test.mjs`
- expected output: full health and server regression passes
- actual output: 23 tests passed, 0 failed
- status: PASS
- commit hash: unavailable; current directory is not a Git repository

```text
ℹ tests 23
ℹ suites 7
ℹ pass 23
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1924.9419
```

## 2026-07-25T14:41:00Z — Final HTTP smoke test

Preliminary note: an initial default-port smoke attempt found `127.0.0.1:3000` already in use. The valid smoke test was rerun with `PORT=0` to bind an ephemeral local port.

- command: `PORT=0 node src/server/server.mjs` plus `curl` requests
- server URL: `http://127.0.0.1:65520`
- expected output: public endpoint and method behavior matches the final contract
- actual output:

```text
GET / -> 200
{"name":"club-of-agents","status":"available","endpoints":[{"path":"/","methods":["GET","HEAD","OPTIONS"],"description":"Service information"},{"path":"/health","methods":["GET","HEAD","OPTIONS"],"description":"Process health check"}]}

HEAD / -> 200 bytes=0
content-type: application/json; charset=utf-8
cache-control: no-store
content-length: 236

GET /health -> 200
{"status":"ok"}

OPTIONS /health -> 204 bytes=0
allow: GET, HEAD, OPTIONS

POST /health -> 405
allow: GET, HEAD, OPTIONS
{"error":"method_not_allowed","allowed":["GET","HEAD","OPTIONS"]}

GET /missing -> 404
{"error":"not_found"}
```

- status: PASS
