import assert from 'node:assert/strict';
import { createServer } from 'node:http';
import { after, before, describe, it } from 'node:test';

import {
  getHealth,
  handleHealthRequest,
  isHealthRequest
} from '../../src/health/health.mjs';

describe('health response contract', () => {
  it('returns the stable health status field', () => {
    assert.deepEqual(getHealth(), { status: 'ok' });
  });

  it('matches only GET /health requests', () => {
    assert.equal(isHealthRequest({ method: 'GET', url: '/health' }), true);
    assert.equal(isHealthRequest({ method: 'GET', url: '/health?verbose=false' }), true);
    assert.equal(isHealthRequest({ method: 'HEAD', url: '/health' }), true);
    assert.equal(isHealthRequest({ method: 'POST', url: '/health' }), false);
    assert.equal(isHealthRequest({ method: 'GET', url: '/not-health' }), false);
  });
});

describe('GET /health integration', () => {
  let server;
  let baseUrl;

  before(async () => {
    server = createServer((request, response) => {
      if (handleHealthRequest(request, response)) {
        return;
      }

      response.writeHead(404, { 'content-type': 'application/json' });
      response.end(JSON.stringify({ error: 'not_found' }));
    });

    await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
    const address = server.address();
    baseUrl = `http://${address.address}:${address.port}`;
  });

  after(async () => {
    await new Promise((resolve, reject) => {
      server.close((error) => (error ? reject(error) : resolve()));
    });
  });

  it('returns HTTP 200 and the documented JSON schema', async () => {
    const response = await fetch(`${baseUrl}/health`);
    const body = await response.json();

    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /^application\/json/);
    assert.deepEqual(body, { status: 'ok' });
  });

  it('returns HTTP 200 and no body for HEAD /health', async () => {
    const response = await fetch(`${baseUrl}/health`, { method: 'HEAD' });
    const body = await response.text();

    assert.equal(response.status, 200);
    assert.match(response.headers.get('content-type'), /^application\/json/);
    assert.equal(body, '');
  });
});
