/**
 * Stable health-check contract for the application process.
 *
 * The endpoint is intentionally dependency-free so it can be mounted by any
 * Node.js HTTP application without pulling in framework infrastructure.
 */
export const HEALTH_RESPONSE = Object.freeze({ status: 'ok' });

export function getHealth() {
  return { ...HEALTH_RESPONSE };
}

export function writeHealthResponse(response, { includeBody = true } = {}) {
  const body = `${JSON.stringify(getHealth())}\n`;

  response.writeHead(200, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'content-length': Buffer.byteLength(body)
  });
  response.end(includeBody ? body : undefined);
}

export function isHealthRequest(request) {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    return false;
  }

  const url = new URL(request.url ?? '/', 'http://localhost');
  return url.pathname === '/health';
}

export function handleHealthRequest(request, response) {
  if (!isHealthRequest(request)) {
    return false;
  }

  writeHealthResponse(response, { includeBody: request.method !== 'HEAD' });
  return true;
}
