import { storageService } from './storageService';
import type { LocalRequest, LocalRequestState, LocalEvacuationVolunteer, LocalReliefVolunteer, SyncStatus } from '../types';

const STORAGE_KEY = 'landslide_requests';
const CURRENT_VERSION = 1;

interface VersionedRequestStore {
  version: number;
  requests: LocalRequest[];
  volunteers: Array<LocalEvacuationVolunteer | LocalReliefVolunteer>;
}

function createInitialStore(): VersionedRequestStore {
  return {
    version: CURRENT_VERSION,
    requests: [],
    volunteers: [],
  };
}

function normalizeSyncStatus(record: Record<string, unknown>): SyncStatus {
  if (record.syncStatus === 'local_only' ||
      record.syncStatus === 'syncing' ||
      record.syncStatus === 'server_confirmed' ||
      record.syncStatus === 'sync_failed') {
    return record.syncStatus;
  }
  return 'local_only';
}

function normalizeRequest(req: Record<string, unknown>): LocalRequest {
  return {
    ...req,
    syncStatus: normalizeSyncStatus(req),
  } as LocalRequest;
}

export async function loadRequests(): Promise<LocalRequestState> {
  try {
    const raw = await storageService.getItem(STORAGE_KEY);
    
    if (!raw) {
      return createInitialStore();
    }

    const parsed = JSON.parse(raw) as Partial<VersionedRequestStore>;
    
    if (parsed.version !== CURRENT_VERSION) {
      console.warn(`[RequestStorage] Version mismatch: expected ${CURRENT_VERSION}, got ${parsed.version}`);
      return createInitialStore();
    }

    if (!Array.isArray(parsed.requests) || !Array.isArray(parsed.volunteers)) {
      console.warn('[RequestStorage] Invalid data structure');
      throw new Error('[RequestStorage] Invalid data structure');
    }

    return {
      requests: parsed.requests.map((r) => normalizeRequest(r as unknown as Record<string, unknown>)),
      volunteers: parsed.volunteers.map((v) => normalizeRequest(v as unknown as Record<string, unknown>)) as Array<LocalEvacuationVolunteer | LocalReliefVolunteer>,
    };
  } catch (error) {
    console.warn('[RequestStorage] Failed to load requests:', error);
    throw error;
  }
}

export async function saveRequests(state: LocalRequestState): Promise<void> {
  try {
    const store: VersionedRequestStore = {
      version: CURRENT_VERSION,
      requests: state.requests,
      volunteers: state.volunteers,
    };
    
    await storageService.setItem(STORAGE_KEY, JSON.stringify(store));
  } catch (error) {
    console.warn('[RequestStorage] Failed to save requests:', error);
  }
}

export async function clearRequests(): Promise<void> {
  try {
    await storageService.removeItem(STORAGE_KEY);
  } catch (error) {
    console.warn('[RequestStorage] Failed to clear requests:', error);
  }
}