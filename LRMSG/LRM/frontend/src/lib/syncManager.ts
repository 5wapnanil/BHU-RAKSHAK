import { QueuedOperation } from '@/types/sync';
import { getDB } from '@/lib/db';

let isSyncing = false;

// Notify React context of changes
export const notifySyncChange = () => {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new Event('sync-status-change'));
  }
};

// Generate unique local ID
export const generateOperationId = () => {
  return 'op_' + Date.now() + '_' + Math.random().toString(36).substring(2, 9);
};

/**
 * Resolve the sync upload endpoint URL based on the active runtime environment.
 * - Respects NEXT_PUBLIC_SYNC_URL if explicitly set.
 * - Dynamically adapts to browser hostname (localhost, 10.0.2.2 emulator, or LAN IP e.g. 192.168.x.x).
 * - Connects to the main FastAPI backend on port 8000 (configurable via NEXT_PUBLIC_API_PORT).
 * - Supports SSR/Node/test fallback to NEXT_PUBLIC_API_URL or localhost:8000.
 */
export const getSyncUploadUrl = (customHost?: string): string => {
  if (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_SYNC_URL) {
    return process.env.NEXT_PUBLIC_SYNC_URL;
  }

  const backendPort = (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_PORT) || '8000';

  if (customHost) {
    return `http://${customHost}:${backendPort}/api/sync/upload`;
  }

  if (typeof window !== 'undefined' && window.location?.hostname) {
    const hostname = window.location.hostname;
    const configuredApi = typeof process !== 'undefined' ? process.env?.NEXT_PUBLIC_API_URL : undefined;
    if (configuredApi && !configuredApi.includes('localhost') && !configuredApi.includes('127.0.0.1')) {
      return `${configuredApi.replace(/\/+$/, '')}/api/sync/upload`;
    }
    // Dynamic host adaptation: preserves developer/mobile client host
    return `http://${hostname}:${backendPort}/api/sync/upload`;
  }

  const base = (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_URL) || `http://localhost:${backendPort}`;
  return `${base.replace(/\/+$/, '')}/api/sync/upload`;
};

export const queueOperation = async (operation: Omit<QueuedOperation, 'id' | 'createdAt' | 'status' | 'retryCount'> & { id?: string }): Promise<QueuedOperation> => {
  const db = await getDB();
  const queuedOp: QueuedOperation = {
    id: operation.id || generateOperationId(),
    createdAt: Date.now(),
    status: 'PENDING',
    retryCount: 0,
    operationType: operation.operationType,
    entityType: operation.entityType,
    payload: operation.payload
  };
  
  if (db) {
    await db.put('pending_sync', queuedOp);
    notifySyncChange();
  }
  
  return queuedOp;
};

export const getPendingOperations = async (): Promise<QueuedOperation[]> => {
  const db = await getDB();
  if (!db) return [];
  const allOps = await db.getAll('pending_sync');
  // Return only PENDING and FAILED that we can retry
  return allOps.filter(op => op.status === 'PENDING' || op.status === 'FAILED');
};

export const updateOperationStatus = async (
  id: string,
  status: QueuedOperation['status'],
  incrementRetry = false
) => {
  const db = await getDB();
  if (!db) return;
  const op = await db.get('pending_sync', id);
  if (op) {
    op.status = status;
    if (incrementRetry || status === 'FAILED') op.retryCount += 1;
    await db.put('pending_sync', op);
  }
};

export const processSyncQueue = async () => {
  if (isSyncing || typeof window === 'undefined' || !navigator.onLine) return;
  
  const pendingOps = await getPendingOperations();
  if (pendingOps.length === 0) return;

  isSyncing = true;
  notifySyncChange();
  
  try {
    // Mark them as SYNCING locally while in-flight
    for (const op of pendingOps) {
      await updateOperationStatus(op.id, 'SYNCING');
    }
    notifySyncChange();

    const payload = {
      operations: pendingOps.map(op => ({
        id: op.id,
        operation: op.operationType,
        entity: op.entityType,
        payload: op.payload,
        createdAt: new Date(op.createdAt).toISOString()
      }))
    };

    const targetUrl = getSyncUploadUrl();

    let res: Response;
    try {
      res = await fetch(targetUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
    } catch (networkErr) {
      console.warn("Network error during sync upload to", targetUrl, networkErr);
      // Network failure / unreachable: Preserve records, revert to PENDING with retry count incremented
      for (const op of pendingOps) {
        await updateOperationStatus(op.id, 'PENDING', true);
      }
      return;
    }

    if (res.ok) {
      const data = await res.json();
      const successIds: string[] = Array.isArray(data?.success_ids) ? data.success_ids : [];
      const failIds: string[] = Array.isArray(data?.failed_ids) ? data.failed_ids : [];

      for (const op of pendingOps) {
        if (successIds.includes(op.id)) {
          // Strictly confirm receipt before marking SYNCED
          await updateOperationStatus(op.id, 'SYNCED');
        } else if (failIds.includes(op.id)) {
          // Server explicitly rejected this operation
          await updateOperationStatus(op.id, 'FAILED', true);
        } else {
          // Unacknowledged by server: keep PENDING for retry
          await updateOperationStatus(op.id, 'PENDING', true);
        }
      }
    } else if (res.status >= 500) {
      // Server error (5xx): transient failure, keep PENDING for retry
      console.warn(`Sync server returned ${res.status}: preserving pending operations`);
      for (const op of pendingOps) {
        await updateOperationStatus(op.id, 'PENDING', true);
      }
    } else {
      // Client error (4xx): rejected request
      console.warn(`Sync request rejected with HTTP ${res.status}`);
      for (const op of pendingOps) {
        await updateOperationStatus(op.id, 'FAILED', true);
      }
    }
  } catch (error) {
    console.error("Sync process failed unexpected error", error);
    for (const op of pendingOps) {
      await updateOperationStatus(op.id, 'PENDING', true);
    }
  } finally {
    isSyncing = false;
    notifySyncChange();
  }
};
