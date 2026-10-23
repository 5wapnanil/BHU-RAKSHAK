import { storageService } from '../../storage/storageService';
import { syncIncidents, createIncidentReportOperation, createSyncBatch, submitFieldReportApi } from '../api';
import { checkNetwork, checkBackendHealth } from '../connectivity/connectivityService';
import type { LocalRequest, SyncStatus, LocalFieldReport } from '../../types';

const QUEUE_STORAGE_KEY = 'landslide_sync_queue';
const QUEUE_VERSION = 1;

export type QueueItemStatus = 'pending' | 'processing' | 'completed' | 'failed_permanent';

export interface SyncQueueItem {
  id: string;
  requestId: string;
  operation: 'CREATE';
  entity: 'incident_report' | 'field_report';
  createdAt: string;
  attemptCount: number;
  lastAttemptAt: string | null;
  nextAttemptAt: string;
  status: QueueItemStatus;
}

interface VersionedQueue {
  version: number;
  items: SyncQueueItem[];
}

function createEmptyQueue(): VersionedQueue {
  return { version: QUEUE_VERSION, items: [] };
}

// ── Persistence ──

export async function loadQueue(): Promise<SyncQueueItem[]> {
  try {
    const raw = await storageService.getItem(QUEUE_STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as Partial<VersionedQueue>;
    if (parsed.version !== QUEUE_VERSION || !Array.isArray(parsed.items)) {
      return [];
    }
    return parsed.items;
  } catch {
    return [];
  }
}

export async function saveQueue(items: SyncQueueItem[]): Promise<void> {
  try {
    const store: VersionedQueue = { version: QUEUE_VERSION, items };
    await storageService.setItem(QUEUE_STORAGE_KEY, JSON.stringify(store));
  } catch (e) {
    console.warn('[SyncQueue] Failed to save queue:', e);
  }
}

// ── Queue operations ──

export function createQueueItem(request: LocalRequest): SyncQueueItem {
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

const BASE_DELAY_MS = 30_000;
const MAX_DELAY_MS = 900_000;
const MAX_ATTEMPTS = 10;
const PERMANENT_ERROR_CODES = [400, 401, 403, 404, 422];

function computeBackoff(attempt: number): number {
  const exp = Math.min(attempt, 8);
  const delay = BASE_DELAY_MS * Math.pow(2, exp);
  const jitter = Math.random() * BASE_DELAY_MS;
  return Math.min(delay + jitter, MAX_DELAY_MS);
}

function isRetryableError(errorCode: string | undefined): boolean {
  if (!errorCode) return true;
  if (errorCode === 'NETWORK_ERROR') return true;
  if (errorCode === 'TIMEOUT') return true;
  if (errorCode === 'BACKEND_UNAVAILABLE') return true;
  if (errorCode === 'UNKNOWN') return true;
  if (errorCode.startsWith('HTTP_5')) return true;
  if (errorCode.startsWith('HTTP_')) {
    const status = parseInt(errorCode.split('_')[1], 10);
    if (PERMANENT_ERROR_CODES.indexOf(status) !== -1) return false;
  }
  return false;
}

// ── Processor ──

let processingLock = false;

export async function processSyncQueue(
  findRequest: (id: string) => LocalRequest | undefined,
  updateSyncStatus: (id: string, syncStatus: SyncStatus) => void
): Promise<number> {
  if (processingLock) return 0;
  processingLock = true;

  try {
    const hasNetwork = await checkNetwork();
    if (!hasNetwork) return 0;

    const backendOk = await checkBackendHealth();
    if (!backendOk) return 0;

    let items = await loadQueue();
    const now = Date.now();
    let processed = 0;

    for (let i = 0; i < items.length; i++) {
      const item = items[i];
      if (item.status !== 'pending') continue;
      if (new Date(item.nextAttemptAt).getTime() > now) continue;

      const request = findRequest(item.requestId);
      if (!request) {
        items[i] = { ...item, status: 'completed' };
        continue;
      }

      items[i] = {
        ...item,
        status: 'processing',
        attemptCount: item.attemptCount + 1,
        lastAttemptAt: new Date().toISOString(),
      };
      await saveQueue(items);

      updateSyncStatus(request.id, 'syncing');

      // ── Branch A: Dedicated FieldReport API submission ──
      if (item.entity === 'field_report' && request.type === 'field_report') {
        const fieldReport = request as LocalFieldReport;
        // Avoid duplicate submission if already confirmed with a serverId
        if (fieldReport.serverId) {
          updateSyncStatus(request.id, 'server_confirmed');
          items[i] = { ...items[i], status: 'completed' };
          await saveQueue(items);
          continue;
        }

        try {
          const result = await submitFieldReportApi(fieldReport.formData);
          if (result.success && result.data) {
            fieldReport.serverId = result.data.id;
            updateSyncStatus(request.id, 'server_confirmed');
            items[i] = { ...items[i], status: 'completed' };
            processed++;
          } else {
            const errorCode = result.error?.code;
            if (!isRetryableError(errorCode)) {
              updateSyncStatus(request.id, 'sync_failed');
              items[i] = { ...items[i], status: 'failed_permanent' };
            } else if (items[i].attemptCount >= MAX_ATTEMPTS) {
              updateSyncStatus(request.id, 'sync_failed');
              items[i] = { ...items[i], status: 'failed_permanent' };
            } else {
              updateSyncStatus(request.id, 'sync_failed');
              const backoff = computeBackoff(items[i].attemptCount);
              items[i] = {
                ...items[i],
                status: 'pending',
                nextAttemptAt: new Date(now + backoff).toISOString(),
              };
            }
          }
        } catch {
          if (items[i].attemptCount >= MAX_ATTEMPTS) {
            updateSyncStatus(request.id, 'sync_failed');
            items[i] = { ...items[i], status: 'failed_permanent' };
          } else {
            updateSyncStatus(request.id, 'sync_failed');
            const backoff = computeBackoff(items[i].attemptCount);
            items[i] = {
              ...items[i],
              status: 'pending',
              nextAttemptAt: new Date(now + backoff).toISOString(),
            };
          }
        }
        await saveQueue(items);
        continue;
      }

      // ── Branch B: General Incident / Coordination requests ──
      const operation = createIncidentReportOperation(request);
      const batch = createSyncBatch([operation]);

      try {
        const result = await syncIncidents(batch);

        if (result.success && result.data) {
          const accepted = result.data.failed_ids.indexOf(request.id) === -1;
          if (accepted) {
            updateSyncStatus(request.id, 'server_confirmed');
            items[i] = { ...items[i], status: 'completed' };
            processed++;
          } else {
            updateSyncStatus(request.id, 'sync_failed');
            if (items[i].attemptCount >= MAX_ATTEMPTS) {
              items[i] = { ...items[i], status: 'failed_permanent' };
            } else {
              const backoff = computeBackoff(items[i].attemptCount);
              items[i] = {
                ...items[i],
                status: 'pending',
                nextAttemptAt: new Date(now + backoff).toISOString(),
              };
            }
          }
        } else {
          const errorCode = result.error?.code;
          if (!isRetryableError(errorCode)) {
            updateSyncStatus(request.id, 'sync_failed');
            items[i] = { ...items[i], status: 'failed_permanent' };
          } else if (items[i].attemptCount >= MAX_ATTEMPTS) {
            updateSyncStatus(request.id, 'sync_failed');
            items[i] = { ...items[i], status: 'failed_permanent' };
          } else {
            updateSyncStatus(request.id, 'sync_failed');
            const backoff = computeBackoff(items[i].attemptCount);
            items[i] = {
              ...items[i],
              status: 'pending',
              nextAttemptAt: new Date(now + backoff).toISOString(),
            };
          }
        }
      } catch {
        if (items[i].attemptCount >= MAX_ATTEMPTS) {
          updateSyncStatus(request.id, 'sync_failed');
          items[i] = { ...items[i], status: 'failed_permanent' };
        } else {
          updateSyncStatus(request.id, 'sync_failed');
          const backoff = computeBackoff(items[i].attemptCount);
          items[i] = {
            ...items[i],
            status: 'pending',
            nextAttemptAt: new Date(now + backoff).toISOString(),
          };
        }
      }

      await saveQueue(items);
    }

    return processed;
  } finally {
    processingLock = false;
  }
}

export async function removeCompletedItems(): Promise<void> {
  const items = await loadQueue();
  const filtered = items.filter((item) => item.status === 'pending' || item.status === 'processing');
  await saveQueue(filtered);
}
