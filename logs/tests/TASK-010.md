# Test Log — TASK-010

## 2026-07-25T13:54:00Z — Node.js health and server regression test

- task ID: TASK-010
- agent ID: 019f9954-0bf4-7d10-94a8-56ef18c92649
- timestamp: 2026-07-25T13:54:00Z
- environment: Windows/Git Bash path `/c/dev/pi/club-of-agents`, Node.js v24.13.1
- command: `node --test tests/health/health.test.mjs tests/server/server.test.mjs`
- input or fixture: health module tests; local HTTP servers started on ephemeral ports; root endpoint request to `GET /`
- expected output: root endpoint test passes; existing health, 404, logging, configuration, and shutdown behavior remains passing
- actual output: 14 tests passed, 0 failed
- pass/fail status: PASS
- log or artifact path: `logs/tests/TASK-010.md`
- commit hash: unavailable; current directory is not a Git repository

```text
▶ health response contract
  ✔ returns the stable health status field (0.9783ms)
  ✔ matches only GET /health requests (0.1779ms)
✔ health response contract (1.8758ms)
▶ GET /health integration
  ✔ returns HTTP 200 and the documented JSON schema (19.4606ms)
✔ GET /health integration (34.1216ms)
▶ server configuration
  ✔ uses safe local defaults (1.0439ms)
  ✔ accepts explicit host and numeric port overrides (0.1194ms)
  ✔ accepts explicit string port overrides (0.1103ms)
  ✔ rejects invalid ports before server bind (0.4226ms)
✔ server configuration (2.5327ms)
▶ application server
  ✔ serves GET / with service metadata and available routes (20.515ms)
  ✔ serves GET /health through the mounted health handler (3.1774ms)
  ✔ returns JSON 404 for unknown routes (1.5ms)
✔ application server (39.5868ms)
▶ request logging
  ✔ logs completed request method, path, status code, and duration (7.193ms)
✔ request logging (9.7202ms)
▶ server shutdown
  ✔ treats missing or already stopped servers as safe no-ops (0.2964ms)
  ✔ closes a running server cleanly (1.0139ms)
  ✔ registers SIGINT and SIGTERM handlers for CLI shutdown (0.224ms)
✔ server shutdown (1.6533ms)
ℹ tests 14
ℹ suites 6
ℹ pass 14
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 1315.9482
```
