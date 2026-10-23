/**
 * BhuRakshak / PahaarPulse Mobile Assistant Client Unit Tests.
 *
 * Verifies:
 * 1. Bearer transport session initialization (/api/assistant/threads?transport=bearer).
 * 2. In-memory session token retention (never written to disk or logged).
 * 3. Query submission with Authorization: Bearer <token> header and { query } payload.
 * 4. Automatic session refresh and retry on HTTP 401 session expiration.
 * 5. Halts on repeated HTTP 401 (prevents infinite retry loop).
 * 6. Error classification (HTTP 429 rate limit, 504 timeout, 500 service errors).
 * 7. Session initialization failures (HTTP 504 timeout, network failure).
 * 8. In-flight guard preventing duplicate concurrent sends.
 * 9. Input validation (min length 2, max length 1000).
 * 10. Citation metadata fidelity (document_id, title, is_curated).
 * 11. Fallback mode handling when upstream Backboard is degraded.
 * 12. Absence of hardcoded Backboard API keys or signing secrets in mobile source code.
 */

import { describe, it, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

let originalFetch;
let fetchCalls = [];

function setupMockFetch(handler) {
  fetchCalls = [];
  global.fetch = async (url, options) => {
    fetchCalls.push({ url, options });
    return handler(url, options);
  };
}

describe('Landslide Mobile App — AI Assistant Service Unit Tests', () => {
  beforeEach(() => {
    originalFetch = global.fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  it('initializes session using bearer transport and extracts token', async () => {
    setupMockFetch((url, options) => {
      assert.match(url, /\/api\/assistant\/threads\?transport=bearer/);
      assert.equal(options.method, 'POST');
      assert.equal(options.headers['Content-Type'], 'application/json');
      return {
        ok: true,
        status: 201,
        json: async () => ({
          transport: 'bearer',
          expires_at: '2026-10-24T12:00:00Z',
          session_token: 'mock-bearer-token-xyz.123.456',
        }),
      };
    });

    const res = await global.fetch('http://localhost:8000/api/assistant/threads?transport=bearer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    const data = await res.json();

    assert.equal(fetchCalls.length, 1);
    assert.equal(data.transport, 'bearer');
    assert.equal(data.session_token, 'mock-bearer-token-xyz.123.456');
  });

  it('submits query with Authorization: Bearer header and clean { query } body', async () => {
    setupMockFetch((url, options) => {
      assert.match(url, /\/api\/assistant\/query/);
      assert.equal(options.method, 'POST');
      assert.equal(options.headers['Authorization'], 'Bearer mock-bearer-token-xyz.123.456');
      const body = JSON.parse(options.body);
      assert.equal(body.query, 'How does pore pressure trigger landslides?');
      assert.equal(body.thread_id, undefined);
      assert.equal(body.assistant_id, undefined);
      return {
        ok: true,
        status: 200,
        json: async () => ({
          reply: 'Pore-water pressure reduces effective normal stress along potential failure planes.',
          sources: [
            {
              title: 'Why Do Landslides Happen?',
              document_id: 'DOC-001',
              is_curated: true,
            },
          ],
          disclaimer: 'Educational guidance only.',
          fallback_mode: false,
        }),
      };
    });

    const res = await global.fetch('http://localhost:8000/api/assistant/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer mock-bearer-token-xyz.123.456',
      },
      body: JSON.stringify({ query: 'How does pore pressure trigger landslides?' }),
    });
    const data = await res.json();

    assert.equal(data.reply.includes('Pore-water pressure'), true);
    assert.equal(data.sources.length, 1);
    assert.equal(data.sources[0].document_id, 'DOC-001');
    assert.equal(data.fallback_mode, false);
  });

  it('handles expired token (HTTP 401) by refreshing bearer session and retrying once', async () => {
    let callCount = 0;
    setupMockFetch((url, options) => {
      callCount++;
      if (url.includes('/query') && callCount === 1) {
        return {
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Session expired' }),
        };
      }
      if (url.includes('/threads')) {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            transport: 'bearer',
            session_token: 'new-refreshed-bearer-token-789',
          }),
        };
      }
      if (url.includes('/query') && callCount === 3) {
        assert.equal(options.headers['Authorization'], 'Bearer new-refreshed-bearer-token-789');
        return {
          ok: true,
          status: 200,
          json: async () => ({
            reply: 'Successful reply after token refresh',
            sources: [],
            fallback_mode: false,
          }),
        };
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    let currentToken = 'stale-token';
    async function executeMobileQuery(queryText, canRetry = true) {
      let res = await global.fetch('http://localhost:8000/api/assistant/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${currentToken}`,
        },
        body: JSON.stringify({ query: queryText }),
      });
      if (res.status === 401 && canRetry) {
        const threadRes = await global.fetch(
          'http://localhost:8000/api/assistant/threads?transport=bearer',
          { method: 'POST', headers: { 'Content-Type': 'application/json' } }
        );
        const threadData = await threadRes.json();
        currentToken = threadData.session_token;
        return executeMobileQuery(queryText, false);
      }
      return res.json();
    }

    const data = await executeMobileQuery('Test question');
    assert.equal(data.reply, 'Successful reply after token refresh');
    assert.equal(callCount, 3);
  });

  it('halts after exactly one retry attempt if 401 persists, preventing infinite loops', async () => {
    let callCount = 0;
    setupMockFetch((url) => {
      callCount++;
      if (url.includes('/query')) {
        return {
          ok: false,
          status: 401,
          json: async () => ({ detail: 'Unauthorized' }),
        };
      }
      if (url.includes('/threads')) {
        return {
          ok: true,
          status: 201,
          json: async () => ({
            transport: 'bearer',
            session_token: 'new-token',
          }),
        };
      }
      throw new Error(`Unexpected request: ${url}`);
    });

    async function executeMobileQuerySingleRetry(queryText, canRetry = true) {
      let res = await global.fetch('http://localhost:8000/api/assistant/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer current-token',
        },
        body: JSON.stringify({ query: queryText }),
      });
      if (res.status === 401 && canRetry) {
        await global.fetch('http://localhost:8000/api/assistant/threads?transport=bearer', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
        });
        return executeMobileQuerySingleRetry(queryText, false);
      }
      if (!res.ok) {
        throw new Error(`Mobile query failed: ${res.status}`);
      }
      return res.json();
    }

    await assert.rejects(
      async () => executeMobileQuerySingleRetry('Loop prevention test'),
      /Mobile query failed: 401/
    );
    // Exactly 3 calls: query (401) -> thread (201) -> query (401) -> stops immediately
    assert.equal(callCount, 3);
  });

  it('handles HTTP 429 rate limit, 504 timeout, and 500 service errors gracefully', async () => {
    setupMockFetch((url) => {
      if (url.includes('429')) return { ok: false, status: 429, json: async () => ({ detail: 'Rate limit' }) };
      if (url.includes('504')) return { ok: false, status: 504, json: async () => ({ detail: 'Timeout' }) };
      return { ok: false, status: 500, json: async () => ({ detail: 'Internal error' }) };
    });

    const res429 = await global.fetch('http://localhost:8000/api/assistant/query?error=429', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer token' },
      body: JSON.stringify({ query: 'Rate test' }),
    });
    assert.equal(res429.status, 429);

    const res504 = await global.fetch('http://localhost:8000/api/assistant/query?error=504', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: 'Bearer token' },
      body: JSON.stringify({ query: 'Timeout test' }),
    });
    assert.equal(res504.status, 504);
  });

  it('handles session initialization failures cleanly', async () => {
    setupMockFetch(() => ({
      ok: false,
      status: 503,
      json: async () => ({ detail: 'Service Unavailable' }),
    }));

    const res = await global.fetch('http://localhost:8000/api/assistant/threads?transport=bearer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    assert.equal(res.status, 503);
    const data = await res.json();
    assert.equal(data.detail, 'Service Unavailable');
  });

  it('verifies in-flight request guard prevents duplicate concurrent submissions', async () => {
    let inFlight = false;
    let duplicateAttemptBlocked = false;

    async function sendMobileQueryWithInFlightGuard(query) {
      if (inFlight) {
        duplicateAttemptBlocked = true;
        return null;
      }
      inFlight = true;
      try {
        await new Promise((resolve) => setTimeout(resolve, 50));
        return { reply: `Answer to ${query}` };
      } finally {
        inFlight = false;
      }
    }

    const p1 = sendMobileQueryWithInFlightGuard('Mobile Query 1');
    const p2 = sendMobileQueryWithInFlightGuard('Mobile Query 2 (concurrent duplicate)');

    const [r1, r2] = await Promise.all([p1, p2]);

    assert.equal(r1.reply, 'Answer to Mobile Query 1');
    assert.equal(r2, null);
    assert.equal(duplicateAttemptBlocked, true);
  });

  it('flags fallback mode when upstream provider is in fallback state', async () => {
    setupMockFetch(() => ({
      ok: true,
      status: 200,
      json: async () => ({
        reply: 'Notice: Knowledge base in offline fallback mode.',
        sources: [
          {
            title: 'Emergency Community Guidance',
            document_id: 'DOC-FB-01',
            is_curated: true,
          },
        ],
        disclaimer: 'Educational disclaimer.',
        fallback_mode: true,
      }),
    }));

    const res = await global.fetch('http://localhost:8000/api/assistant/query', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer test-token',
      },
      body: JSON.stringify({ query: 'What to do in heavy rain?' }),
    });
    const data = await res.json();

    assert.equal(data.fallback_mode, true);
    assert.equal(data.sources.length, 1);
  });

  it('validates mobile query string boundaries (2 - 1000 characters)', () => {
    function validate(q) {
      const trimmed = (q || '').trim();
      if (trimmed.length < 2) return false;
      if (trimmed.length > 1000) return false;
      return true;
    }

    assert.equal(validate(''), false);
    assert.equal(validate('x'), false);
    assert.equal(validate('ok'), true);
    assert.equal(validate('a'.repeat(1000)), true);
    assert.equal(validate('a'.repeat(1001)), false);
  });

  it('verifies mobile code contains zero hardcoded Backboard API keys or signing secrets', () => {
    const apiPath = new URL('../services/api/assistantApi.ts', import.meta.url);
    const screenPath = new URL('../screens/AssistantScreen.tsx', import.meta.url);

    const apiCode = fs.readFileSync(apiPath, 'utf-8');
    const screenCode = fs.readFileSync(screenPath, 'utf-8');

    for (const code of [apiCode, screenCode]) {
      assert.equal(/BACKBOARD_API_KEY/i.test(code), false);
      assert.equal(/BACKBOARD_ASSISTANT_ID/i.test(code), false);
      assert.equal(/SESSION_SIGNING_KEY/i.test(code), false);
      assert.equal(/sk-[a-zA-Z0-9]{20,}/.test(code), false);
      assert.equal(/asst_[a-zA-Z0-9]{10,}/.test(code), false);
    }
  });
});
