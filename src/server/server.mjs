import { createServer } from 'node:http';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

import { handleHealthRequest } from '../health/health.mjs';

export const PUBLIC_ROUTE_METHODS = Object.freeze(['GET', 'HEAD', 'OPTIONS']);

export const SERVICE_INFO = Object.freeze({
  name: 'club-of-agents',
  status: 'available',
  endpoints: Object.freeze([
    Object.freeze({
      path: '/',
      methods: PUBLIC_ROUTE_METHODS,
      description: 'Service information'
    }),
    Object.freeze({
      path: '/health',
      methods: PUBLIC_ROUTE_METHODS,
      description: 'Process health check'
    })
  ])
});

export function getServiceInfo() {
  return {
    ...SERVICE_INFO,
    endpoints: SERVICE_INFO.endpoints.map((endpoint) => ({
      ...endpoint,
      methods: [...endpoint.methods]
    }))
  };
}

export function writeJsonResponse(response, statusCode, payload, { includeBody = true } = {}) {
  const body = `${JSON.stringify(payload)}\n`;
  response.writeHead(statusCode, {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store',
    'content-length': Buffer.byteLength(body)
  });
  response.end(includeBody ? body : undefined);
}

export function getRequestPath(request) {
  const url = new URL(request.url ?? '/', 'http://localhost');
  return url.pathname;
}

export function attachRequestLogging(request, response, logger) {
  if (typeof logger !== 'function') {
    return;
  }

  const startedAt = process.hrtime.bigint();

  response.once('finish', () => {
    const durationMs = Number(process.hrtime.bigint() - startedAt) / 1_000_000;

    try {
      logger({
        method: request.method ?? 'UNKNOWN',
        path: getRequestPath(request),
        statusCode: response.statusCode,
        durationMs
      });
    } catch {
      // Logging must not alter response behavior.
    }
  });
}

export function writeMethodNotAllowedResponse(response, allowedMethods = PUBLIC_ROUTE_METHODS) {
  response.setHeader('allow', allowedMethods.join(', '));
  writeJsonResponse(response, 405, {
    error: 'method_not_allowed',
    allowed: allowedMethods
  });
}

export function writeOptionsResponse(response, allowedMethods = PUBLIC_ROUTE_METHODS) {
  response.writeHead(204, {
    allow: allowedMethods.join(', '),
    'cache-control': 'no-store',
    'content-length': 0
  });
  response.end();
}

export function handleRootRequest(request, response) {
  if (getRequestPath(request) !== '/') {
    return false;
  }

  if (request.method === 'OPTIONS') {
    writeOptionsResponse(response);
    return true;
  }

  if (request.method !== 'GET' && request.method !== 'HEAD') {
    writeMethodNotAllowedResponse(response);
    return true;
  }

  writeJsonResponse(response, 200, getServiceInfo(), { includeBody: request.method !== 'HEAD' });
  return true;
}

export function handleKnownRouteMethod(request, response) {
  if (request.method === 'GET' || request.method === 'HEAD') {
    return false;
  }

  if (getRequestPath(request) === '/health') {
    if (request.method === 'OPTIONS') {
      writeOptionsResponse(response);
      return true;
    }

    writeMethodNotAllowedResponse(response);
    return true;
  }

  return false;
}

export function createApplicationServer({ logger } = {}) {
  return createServer((request, response) => {
    attachRequestLogging(request, response, logger);

    if (handleRootRequest(request, response)) {
      return;
    }

    if (handleHealthRequest(request, response)) {
      return;
    }

    if (handleKnownRouteMethod(request, response)) {
      return;
    }

    writeJsonResponse(response, 404, { error: 'not_found' });
  });
}

export function parseServerConfig({ host = process.env.HOST, port = process.env.PORT } = {}) {
  const resolvedHost = host ?? '127.0.0.1';
  const resolvedPort = port ?? '3000';
  const parsedPort = typeof resolvedPort === 'number' ? resolvedPort : Number(resolvedPort);

  if (!Number.isInteger(parsedPort) || parsedPort < 0 || parsedPort > 65_535) {
    throw new RangeError('PORT must be an integer between 0 and 65535');
  }

  return {
    host: String(resolvedHost),
    port: parsedPort
  };
}

export async function startServer({ host, port, logger } = {}) {
  const config = parseServerConfig({ host, port });
  const server = createApplicationServer({ logger });

  await new Promise((resolve, reject) => {
    server.once('error', reject);
    server.listen(config.port, config.host, () => {
      server.off('error', reject);
      resolve();
    });
  });

  const address = server.address();
  return { server, address };
}

export async function stopServer(server) {
  if (!server?.listening) {
    return;
  }

  await new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

export function installShutdownHandlers(
  server,
  { logger = console.error, exit = process.exit, processLike = process } = {}
) {
  let shuttingDown = false;

  const shutdown = async () => {
    if (shuttingDown) {
      return;
    }

    shuttingDown = true;

    try {
      await stopServer(server);
      exit(0);
    } catch (error) {
      logger(error);
      exit(1);
    }
  };

  processLike.once('SIGINT', shutdown);
  processLike.once('SIGTERM', shutdown);

  return shutdown;
}

export function isDirectCliEntry(metaUrl = import.meta.url, argv = process.argv) {
  return Boolean(argv[1]) && metaUrl === pathToFileURL(resolve(argv[1])).href;
}

if (isDirectCliEntry()) {
  const { server, address } = await startServer();
  installShutdownHandlers(server);
  const displayHost = address.address.includes(':') ? `[${address.address}]` : address.address;
  console.log(`Server listening on http://${displayHost}:${address.port}`);
}
