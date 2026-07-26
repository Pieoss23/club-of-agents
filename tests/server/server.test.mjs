import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { once } from 'node:events';
import { after, before, describe, it } from 'node:test';

import {
  installShutdownHandlers,
  isDirectCliEntry,
  parseServerConfig,
  startServer,
  stopServer
} from '../../src/server/server.mjs';

describe('server configuration', () => {
  it('uses safe local defaults', () => {
    assert.deepEqual(parseServerConfig({}), { host: '127.0.0.1', port: 3000 });
  });

  it('accepts explicit host and numeric port overrides', () => {
    assert.deepEqual(parseServerConfig({ host: '0.0.0.0', port: 8080 }), {
      host: '0.0.0.0',
      port: 8080
    });
  });

  it('accepts explicit string port overrides', () => {
    assert.deepEqual(parseServerConfig({ host: 'localhost', port: '3001' }), {
      host: 'localhost',
      port: 3001
    });
  });

  it('rejects invalid ports before server bind', () => {
    assert.throws(() => parseServerConfig({ port: 'abc' }), /PORT must be an integer/);
    assert.throws(() => parseServerConfig({ port: 65_536 }), /PORT must be an integer/);
    assert.throws(() => parseServerConfig({ port: -1 }), /PORT must be an integer/);
    assert.throws(() => parseServerConfig({ port: 1.5 }), /PORT must be an integer/);
  });
});

describe('application server', () => {
  let server;
  let baseUrl;

  before(async () => {
    const started = await startServer({ host: '127.0.0.1', port: 0 });
    server = started.server;
    const address = started.address;
    baseUrl = `http://${address.address}:${address.port}`;
  });

  after(async () => {
    await stopServer(server);
  });

  it('serves GET / with service metadata and available routes', async () => {
    const response = await fetch(`${baseUrl}/`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /^application\/json/);
    assert.equal(body.name, 'club-of-agents');
    assert.equal(body.status, 'available');
    assert.deepEqual(body.endpoints, [
      {
        path: '/',
        methods: ['GET', 'HEAD', 'OPTIONS'],
        description: 'Service information'
      },
      {
        path: '/health',
        methods: ['GET', 'HEAD', 'OPTIONS'],
        description: 'Process health check'
      }
    ]);
    assert.equal(Object.hasOwn(body, 'env'), false);
    assert.equal(Object.hasOwn(body, 'secrets'), false);
  });

  it('serves GET /health through the mounted health handler', async () => {
    const response = await fetch(`${baseUrl}/health`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.deepEqual(body, { status: 'ok' });
  });

  it('serves HEAD / with service metadata headers and no body', async () => {
    const response = await fetch(`${baseUrl}/`, { method: 'HEAD' });
    const body = await response.text();

    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /^application\/json/);
    assert.equal(body, '');
  });

  it('serves HEAD /health through the mounted health handler with no body', async () => {
    const response = await fetch(`${baseUrl}/health`, { method: 'HEAD' });
    const body = await response.text();

    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /^application\/json/);
    assert.equal(body, '');
  });

  it('returns HTTP 204 for OPTIONS / with allowed methods and no body', async () => {
    const response = await fetch(`${baseUrl}/`, { method: 'OPTIONS' });
    const body = await response.text();

    assert.equal(response.status, 204);
    assert.equal(response.headers.get('allow'), 'GET, HEAD, OPTIONS');
    assert.equal(body, '');
  });

  it('returns HTTP 204 for OPTIONS /health with allowed methods and no body', async () => {
    const response = await fetch(`${baseUrl}/health`, { method: 'OPTIONS' });
    const body = await response.text();

    assert.equal(response.status, 204);
    assert.equal(response.headers.get('allow'), 'GET, HEAD, OPTIONS');
    assert.equal(body, '');
  });

  it('returns JSON 405 for unsupported methods on /', async () => {
    const response = await fetch(`${baseUrl}/`, { method: 'POST' });
    const body = await response.json();

    assert.equal(response.status, 405);
    assert.equal(response.headers.get('allow'), 'GET, HEAD, OPTIONS');
    assert.deepEqual(body, {
      error: 'method_not_allowed',
      allowed: ['GET', 'HEAD', 'OPTIONS']
    });
  });

  it('returns JSON 405 for unsupported methods on /health', async () => {
    const response = await fetch(`${baseUrl}/health`, { method: 'POST' });
    const body = await response.json();

    assert.equal(response.status, 405);
    assert.equal(response.headers.get('allow'), 'GET, HEAD, OPTIONS');
    assert.deepEqual(body, {
      error: 'method_not_allowed',
      allowed: ['GET', 'HEAD', 'OPTIONS']
    });
  });

  it('returns JSON 404 for unknown routes', async () => {
    const response = await fetch(`${baseUrl}/unknown`, { method: 'POST' });
    const body = await response.json();

    assert.equal(response.status, 404);
    assert.match(response.headers.get('content-type'), /^application\/json/);
    assert.deepEqual(body, { error: 'not_found' });
  });
});

describe('request logging', () => {
  let server;
  let baseUrl;
  const logs = [];

  before(async () => {
    const started = await startServer({
      host: '127.0.0.1',
      port: 0,
      logger: (entry) => logs.push(entry)
    });
    server = started.server;
    const address = started.address;
    baseUrl = `http://${address.address}:${address.port}`;
  });

  after(async () => {
    await stopServer(server);
  });

  it('logs completed request method, path, status code, and duration', async () => {
    const response = await fetch(`${baseUrl}/health?token=secret`);
    await response.text();

    assert.equal(response.status, 200);

    const log = await waitForLog(logs, 0);
    assert.equal(log.method, 'GET');
    assert.equal(log.path, '/health');
    assert.equal(log.statusCode, 200);
    assert.equal(typeof log.durationMs, 'number');
    assert.ok(log.durationMs >= 0);
    assert.equal(Object.hasOwn(log, 'body'), false);
    assert.equal(log.path.includes('token=secret'), false);
  });
});

describe('direct CLI startup', () => {
  it('detects direct script execution from relative argv path', () => {
    assert.equal(
      isDirectCliEntry(new URL('../../src/server/server.mjs', import.meta.url).href, [
        process.execPath,
        'src/server/server.mjs'
      ]),
      true
    );
  });

  it('starts with node src/server/server.mjs and serves GET /health', async () => {
    const child = spawn(process.execPath, ['src/server/server.mjs'], {
      env: { ...process.env, PORT: '0' },
      stdio: ['ignore', 'pipe', 'pipe']
    });

    try {
      const [output] = await once(child.stdout, 'data');
      const text = output.toString('utf8');
      const match = text.match(/http:\/\/(.+):(\d+)/);
      assert.ok(match, `Expected listening URL in ${text}`);

      const response = await fetch(`http://${match[1]}:${match[2]}/health`);
      assert.equal(response.status, 200);
      assert.deepEqual(await response.json(), { status: 'ok' });
    } finally {
      child.kill('SIGTERM');
      await once(child, 'exit');
    }
  });
});

describe('server shutdown', () => {
  it('treats missing or already stopped servers as safe no-ops', async () => {
    await assert.doesNotReject(() => stopServer());
    await assert.doesNotReject(() => stopServer({ listening: false }));
  });

  it('closes a running server cleanly', async () => {
    const started = await startServer({ host: '127.0.0.1', port: 0 });

    assert.equal(started.server.listening, true);
    await stopServer(started.server);
    assert.equal(started.server.listening, false);
  });

  it('registers SIGINT and SIGTERM handlers for CLI shutdown', () => {
    const signals = [];
    const fakeProcess = {
      once: (signal, handler) => signals.push([signal, handler])
    };

    const shutdown = installShutdownHandlers(
      { listening: false },
      { processLike: fakeProcess, exit: () => {}, logger: () => {} }
    );

    assert.equal(typeof shutdown, 'function');
    assert.deepEqual(signals.map(([signal]) => signal), ['SIGINT', 'SIGTERM']);
    assert.equal(signals.every(([, handler]) => handler === shutdown), true);
  });
});

async function waitForLog(logs, index) {
  for (let attempt = 0; attempt < 10; attempt += 1) {
    if (logs[index]) {
      return logs[index];
    }

    await new Promise((resolve) => setTimeout(resolve, 5));
  }

  assert.fail(`Expected log entry at index ${index}`);
}
