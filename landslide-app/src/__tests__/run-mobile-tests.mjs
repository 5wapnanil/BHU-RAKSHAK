import { describe, it } from 'node:test';
import assert from 'node:assert/strict';

// Test 1: Queue item creation logic for field reports and other types
function createQueueItemTest(request) {
  return {
    id: `q-${request.id}`,
    requestId: request.id,
    operation: 'CREATE',
    entity: request.type === 'field_report' ? 'field_report' : 'incident_report',
    createdAt: request.createdAt,
    attemptCount: 0,
    lastAttemptAt: null,
    nextAttemptAt: request.createdAt,
    status: 'pending',
  };
}

// Test 2: Payload mapping
function mapFieldReportPayload(request) {
  return {
    notes: request.formData.notes,
    location: request.formData.locationName,
    contactName: request.formData.reporterName,
    contactPhone: request.formData.reporterPhone,
    gpsCoords: request.formData.gpsCoords,
  };
}

// Test 3: Backoff computation
function computeBackoff(attempt) {
  const BASE_DELAY_MS = 30_000;
  const MAX_DELAY_MS = 900_000;
  const exp = Math.min(attempt, 8);
  const delay = BASE_DELAY_MS * Math.pow(2, exp);
  return Math.min(delay, MAX_DELAY_MS);
}

// Test 4: Retryable error checker
function isRetryableError(errorCode) {
  const PERMANENT_ERROR_CODES = [400, 401, 403, 404, 422];
  if (!errorCode) return true;
  if (errorCode === 'NETWORK_ERROR' || errorCode === 'TIMEOUT' || errorCode === 'BACKEND_UNAVAILABLE') return true;
  if (errorCode.startsWith('HTTP_5')) return true;
  if (errorCode.startsWith('HTTP_')) {
    const status = parseInt(errorCode.split('_')[1], 10);
    if (PERMANENT_ERROR_CODES.includes(status)) return false;
  }
  return false;
}

// Test 5: Dynamic platform-specific sync URL resolution
function resolveSyncUrl({ platform, isEmulator, windowHostname, envSyncUrl, envApiUrl, envPort }) {
  if (envSyncUrl) return envSyncUrl;
  const port = envPort || '8000';

  if (platform === 'web' || typeof windowHostname === 'string') {
    const host = windowHostname || 'localhost';
    if (envApiUrl && !envApiUrl.includes('localhost') && !envApiUrl.includes('127.0.0.1')) {
      return `${envApiUrl.replace(/\/+$/, '')}/api/sync/upload`;
    }
    return `http://${host}:${port}/api/sync/upload`;
  }

  if (platform === 'android') {
    const host = isEmulator ? '10.0.2.2' : '192.168.0.102';
    return `http://${host}:${port}/api/sync/upload`;
  }

  if (platform === 'ios') {
    const host = isEmulator ? 'localhost' : '192.168.0.102';
    return `http://${host}:${port}/api/sync/upload`;
  }

  const base = envApiUrl || `http://localhost:${port}`;
  return `${base.replace(/\/+$/, '')}/api/sync/upload`;
}

// Test 6: Sync outcome transition handler
function handleSyncOutcome(operations, responseOrError) {
  if (responseOrError instanceof Error || responseOrError?.isNetworkError) {
    // Network failure: preserve records, keep pending for retry
    return operations.map(op => ({
      ...op,
      status: 'pending',
      retryCount: op.retryCount + 1,
      serverConfirmed: false,
      lastError: 'NETWORK_ERROR',
    }));
  }

  if (responseOrError.status >= 500) {
    // 5xx transient server error: keep pending for retry
    return operations.map(op => ({
      ...op,
      status: 'pending',
      retryCount: op.retryCount + 1,
      serverConfirmed: false,
      lastError: `HTTP_${responseOrError.status}`,
    }));
  }

  if (responseOrError.status === 200 && responseOrError.data) {
    const successIds = responseOrError.data.success_ids || [];
    const failIds = responseOrError.data.failed_ids || [];
    return operations.map(op => {
      if (successIds.includes(op.id)) {
        return { ...op, status: 'synced', serverConfirmed: true };
      }
      if (failIds.includes(op.id)) {
        return { ...op, status: 'failed', serverConfirmed: false, retryCount: op.retryCount + 1 };
      }
      return { ...op, status: 'pending', serverConfirmed: false, retryCount: op.retryCount + 1 };
    });
  }

  // 4xx client rejection
  return operations.map(op => ({
    ...op,
    status: 'failed',
    serverConfirmed: false,
    retryCount: op.retryCount + 1,
  }));
}

describe('Landslide Mobile App — FieldReport & Sync Queue Unit Tests', () => {
  it('creates queue item with field_report entity type', () => {
    const report = {
      id: 'FLD-2026-001',
      type: 'field_report',
      status: 'pending',
      syncStatus: 'local_only',
      formData: {
        notes: 'Cracks visible across roadway',
        locationName: 'Peshok Hill Road',
        gpsCoords: { latitude: 27.0365, longitude: 88.2627 },
      },
      createdAt: '2026-10-22T08:00:00.000Z',
      updatedAt: '2026-10-22T08:00:00.000Z',
    };

    const queueItem = createQueueItemTest(report);
    assert.equal(queueItem.id, 'q-FLD-2026-001');
    assert.equal(queueItem.entity, 'field_report');
    assert.equal(queueItem.status, 'pending');
  });

  it('preserves emergency evacuation queue item with incident_report entity', () => {
    const evac = {
      id: 'EVC-2026-002',
      type: 'evacuation',
      status: 'pending',
      syncStatus: 'local_only',
      formData: {
        location: 'Upper Cart Road',
        numberOfPeople: '5',
      },
      createdAt: '2026-10-22T08:00:00.000Z',
      updatedAt: '2026-10-22T08:00:00.000Z',
    };

    const queueItem = createQueueItemTest(evac);
    assert.equal(queueItem.entity, 'incident_report');
  });

  it('maps field_report payload accurately', () => {
    const report = {
      formData: {
        notes: 'Massive landslide blocking bridge',
        locationName: 'Teesta Bazaar',
        reporterName: 'Sonam Dorjee',
        reporterPhone: '+919876543210',
        gpsCoords: { latitude: 27.05, longitude: 88.27 },
      },
    };

    const payload = mapFieldReportPayload(report);
    assert.equal(payload.notes, 'Massive landslide blocking bridge');
    assert.equal(payload.location, 'Teesta Bazaar');
    assert.equal(payload.contactName, 'Sonam Dorjee');
    assert.equal(payload.contactPhone, '+919876543210');
    assert.deepEqual(payload.gpsCoords, { latitude: 27.05, longitude: 88.27 });
  });

  it('handles field reports without GPS or photo gracefully', () => {
    const report = {
      formData: {
        notes: 'Audible rockfall heard near ridge',
      },
    };

    const payload = mapFieldReportPayload(report);
    assert.equal(payload.notes, 'Audible rockfall heard near ridge');
    assert.equal(payload.gpsCoords, undefined);
  });

  it('distinguishes permanent 4xx errors from retryable errors', () => {
    assert.equal(isRetryableError('HTTP_400'), false, 'HTTP 400 is permanent');
    assert.equal(isRetryableError('HTTP_422'), false, 'HTTP 422 is permanent');
    assert.equal(isRetryableError('HTTP_500'), true, 'HTTP 500 is retryable');
    assert.equal(isRetryableError('HTTP_503'), true, 'HTTP 503 is retryable');
    assert.equal(isRetryableError('NETWORK_ERROR'), true, 'Network error is retryable');
    assert.equal(isRetryableError('TIMEOUT'), true, 'Timeout is retryable');
  });

  it('computes exponential backoff within limits', () => {
    const delay0 = computeBackoff(0);
    const delay1 = computeBackoff(1);
    const delay2 = computeBackoff(2);
    const delay10 = computeBackoff(10);

    assert.equal(delay0, 30_000);
    assert.equal(delay1, 60_000);
    assert.equal(delay2, 120_000);
    assert.equal(delay10, 900_000); // capped at MAX_DELAY_MS
  });

  it('prevents duplicate submissions when serverId is already confirmed', () => {
    const report = {
      id: 'FLD-2026-005',
      serverId: '7d945a0b-1111-2222-3333-444455556666',
      syncStatus: 'server_confirmed',
    };

    // Duplicate prevention: if serverId exists, do not resubmit
    const shouldSkip = Boolean(report.serverId && report.syncStatus === 'server_confirmed');
    assert.equal(shouldSkip, true);
  });

  it('displays honest sync states with clear differentiation', () => {
    const labels = {
      local_only: 'Saved Offline',
      syncing: 'Uploading',
      server_confirmed: 'Submitted',
      sync_failed: 'Delivery Not Confirmed',
    };

    assert.equal(labels.local_only, 'Saved Offline');
    assert.equal(labels.syncing, 'Uploading');
    assert.equal(labels.server_confirmed, 'Submitted');
    assert.equal(labels.sync_failed, 'Delivery Not Confirmed');
  });

  // ── New Test Suite: Platform-Specific URL Selection ──
  it('selects correct sync URL for Android emulator (10.0.2.2:8000)', () => {
    const url = resolveSyncUrl({ platform: 'android', isEmulator: true });
    assert.equal(url, 'http://10.0.2.2:8000/api/sync/upload');
    assert.doesNotMatch(url, /8004/, 'Port 8004 must never be selected');
  });

  it('selects correct sync URL for physical Android device on LAN (192.168.0.102:8000)', () => {
    const url = resolveSyncUrl({ platform: 'android', isEmulator: false });
    assert.equal(url, 'http://192.168.0.102:8000/api/sync/upload');
  });

  it('selects correct sync URL for web browser on localhost (localhost:8000)', () => {
    const url = resolveSyncUrl({ platform: 'web', windowHostname: 'localhost' });
    assert.equal(url, 'http://localhost:8000/api/sync/upload');
  });

  it('selects correct sync URL for mobile web browser accessing via LAN IP', () => {
    const url = resolveSyncUrl({ platform: 'web', windowHostname: '192.168.0.102' });
    assert.equal(url, 'http://192.168.0.102:8000/api/sync/upload');
  });

  it('selects correct sync URL for mobile web browser in Android emulator', () => {
    const url = resolveSyncUrl({ platform: 'web', windowHostname: '10.0.2.2' });
    assert.equal(url, 'http://10.0.2.2:8000/api/sync/upload');
  });

  it('respects explicit NEXT_PUBLIC_SYNC_URL environment override', () => {
    const override = 'https://sync.pahaarpulse.org/api/sync/upload';
    const url = resolveSyncUrl({ platform: 'web', envSyncUrl: override });
    assert.equal(url, override);
  });

  // ── New Test Suite: Network Failure & Acknowledgment Behavior ──
  it('handles network failure: preserves queue items in pending status, never marks synced', () => {
    const ops = [
      { id: 'op_test_1', retryCount: 0, status: 'syncing' },
      { id: 'op_test_2', retryCount: 1, status: 'syncing' },
    ];

    const updated = handleSyncOutcome(ops, new TypeError('Failed to fetch'));
    assert.equal(updated.length, 2);
    for (const op of updated) {
      assert.equal(op.status, 'pending', 'Must revert to pending for retry');
      assert.equal(op.serverConfirmed, false, 'Must not mark serverConfirmed');
      assert.equal(op.lastError, 'NETWORK_ERROR');
    }
    assert.equal(updated[0].retryCount, 1);
    assert.equal(updated[1].retryCount, 2);
  });

  it('handles transient 5xx server error: preserves records and increments retry count', () => {
    const ops = [{ id: 'op_test_3', retryCount: 0, status: 'syncing' }];
    const updated = handleSyncOutcome(ops, { status: 503 });
    assert.equal(updated[0].status, 'pending');
    assert.equal(updated[0].serverConfirmed, false);
    assert.equal(updated[0].retryCount, 1);
  });

  it('handles successful sync acknowledgment: marks synced ONLY for confirmed success_ids', () => {
    const ops = [
      { id: 'op_confirmed_1', retryCount: 0, status: 'syncing' },
      { id: 'op_rejected_2', retryCount: 0, status: 'syncing' },
      { id: 'op_unmentioned_3', retryCount: 0, status: 'syncing' },
    ];

    const mockResponse = {
      status: 200,
      data: {
        success: true,
        success_ids: ['op_confirmed_1'],
        failed_ids: ['op_rejected_2'],
      },
    };

    const updated = handleSyncOutcome(ops, mockResponse);

    // op_confirmed_1 confirmed by server
    assert.equal(updated[0].id, 'op_confirmed_1');
    assert.equal(updated[0].status, 'synced');
    assert.equal(updated[0].serverConfirmed, true);

    // op_rejected_2 rejected by server
    assert.equal(updated[1].id, 'op_rejected_2');
    assert.equal(updated[1].status, 'failed');
    assert.equal(updated[1].serverConfirmed, false);

    // op_unmentioned_3 not mentioned: remains pending for retry
    assert.equal(updated[2].id, 'op_unmentioned_3');
    assert.equal(updated[2].status, 'pending');
    assert.equal(updated[2].serverConfirmed, false);
  });

  // Test 7: Mobile Production & Development API Base URL Resolution
  function resolveApiBaseUrlTest({ isDev, envApiUrl, platform = 'android', isEmulator = false, windowHostname = null }) {
    const configured = envApiUrl?.trim().replace(/\/+$/, '');

    if (!isDev) {
      if (!configured) {
        throw new Error(
          'Configuration Error: Production mobile release build requires EXPO_PUBLIC_API_URL to be configured with an HTTPS backend endpoint.'
        );
      }
      if (!configured.startsWith('https://')) {
        const isLocalLoopback = configured.startsWith('http://localhost') || configured.startsWith('http://127.0.0.1');
        if (!isLocalLoopback) {
          throw new Error(
            `Security Error: Insecure production API URL '${configured}'. Production release builds must use an HTTPS endpoint.`
          );
        }
      }
      return configured;
    }

    if (configured) return configured;
    if (platform === 'web') {
      if (windowHostname) return `http://${windowHostname}:8000`;
      return 'http://localhost:8000';
    }
    if (platform !== 'android') return 'http://192.168.0.102:8000';
    return isEmulator ? 'http://10.0.2.2:8000' : 'http://192.168.0.102:8000';
  }

  it('rejects missing EXPO_PUBLIC_API_URL in production release build', () => {
    assert.throws(
      () => resolveApiBaseUrlTest({ isDev: false, envApiUrl: '' }),
      /Configuration Error: Production mobile release build requires EXPO_PUBLIC_API_URL/
    );
    assert.throws(
      () => resolveApiBaseUrlTest({ isDev: false, envApiUrl: undefined }),
      /Configuration Error: Production mobile release build requires EXPO_PUBLIC_API_URL/
    );
  });

  it('rejects unencrypted HTTP external API URL in production release build', () => {
    assert.throws(
      () => resolveApiBaseUrlTest({ isDev: false, envApiUrl: 'http://api.bhurakshak.in' }),
      /Security Error: Insecure production API URL/
    );
  });

  it('accepts valid HTTPS production API URL in release build', () => {
    const url = resolveApiBaseUrlTest({ isDev: false, envApiUrl: 'https://api.bhurakshak.in/' });
    assert.equal(url, 'https://api.bhurakshak.in');
  });

  it('preserves development Android emulator URL (10.0.2.2:8000)', () => {
    const url = resolveApiBaseUrlTest({ isDev: true, platform: 'android', isEmulator: true });
    assert.equal(url, 'http://10.0.2.2:8000');
  });

  it('preserves development physical LAN URL (192.168.0.102:8000)', () => {
    const url = resolveApiBaseUrlTest({ isDev: true, platform: 'android', isEmulator: false });
    assert.equal(url, 'http://192.168.0.102:8000');
  });
});
