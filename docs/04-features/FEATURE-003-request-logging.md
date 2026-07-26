# FEATURE-003: Server request logging

## Summary

The HTTP server supports an injectable, dependency-free request logging hook for observability.

## Behavior

When `startServer` or `createApplicationServer` receives a `logger` function, the server calls it after each response finishes with:

- `method`: HTTP method, or `UNKNOWN` when unavailable;
- `path`: URL pathname only;
- `statusCode`: final response status code;
- `durationMs`: elapsed response time in milliseconds.

## Privacy and safety

The log entry excludes query strings and request bodies. Logger failures are caught so observability code does not alter response behavior.

## Example

```js
await startServer({
  logger: (entry) => console.log(JSON.stringify(entry))
});
```

Example log entry:

```json
{"method":"GET","path":"/health","statusCode":200,"durationMs":1.2}
```

## Tests

Evidence is recorded in `logs/tests/TASK-003.md`.
