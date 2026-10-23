import { useRequestStore } from '../services/store/RequestStoreContext';
import { syncIncidents, createIncidentReportOperation, createSyncBatch, submitFieldReportApi } from '../services/api';
import { createQueueItem, saveQueue, loadQueue } from '../services/sync';
import type { SyncResponse, ApiResponse } from '../services/api/types';
import type {
  LocalRequest,
  LocalEvacuationRequest,
  LocalHelpRequest,
  LocalReliefRequest,
  LocalEvacuationVolunteer,
  LocalReliefVolunteer,
  LocalFieldReport,
  FieldReportFormData,
  RequestStatus,
  SyncStatus,
} from '../types';

let counter = 0;
function generateId(prefix: string): string {
  counter += 1;
  const ts = Date.now().toString(36);
  return `${prefix}-${ts}-${counter}`;
}

export interface SyncResult {
  local: boolean;
  backend: ApiResponse<SyncResponse> | null;
  serverConfirmed: boolean;
}

let enqueueLock = false;

async function enqueueRequest(request: LocalRequest): Promise<void> {
  if (enqueueLock) return;
  enqueueLock = true;
  try {
    const queue = await loadQueue();
    const exists = queue.some((item) => item.requestId === request.id);
    if (!exists) {
      queue.push(createQueueItem(request));
      await saveQueue(queue);
    }
  } finally {
    enqueueLock = false;
  }
}

export function useLocalRequests() {
  const { state, dispatch } = useRequestStore();

  function updateSyncStatus(id: string, syncStatus: SyncStatus) {
    dispatch({ type: 'UPDATE_SYNC_STATUS', payload: { id, syncStatus } });
  }

  // ── Requests ──

  function addEvacuationRequest(
    data: LocalEvacuationRequest['formData'],
  ): LocalEvacuationRequest {
    const now = new Date().toISOString();
    const req: LocalEvacuationRequest = {
      id: generateId('EVC'),
      type: 'evacuation',
      status: 'pending',
      syncStatus: 'local_only',
      formData: data,
      createdAt: now,
      updatedAt: now,
    };
    dispatch({ type: 'ADD_REQUEST', payload: req });
    enqueueRequest(req);
    return req;
  }

  function addHelpRequest(
    data: LocalHelpRequest['formData'],
  ): LocalHelpRequest {
    const now = new Date().toISOString();
    const req: LocalHelpRequest = {
      id: generateId('HLP'),
      type: 'help',
      status: 'pending',
      syncStatus: 'local_only',
      formData: data,
      createdAt: now,
      updatedAt: now,
    };
    dispatch({ type: 'ADD_REQUEST', payload: req });
    enqueueRequest(req);
    return req;
  }

  function addEvacuationVolunteer(
    data: LocalEvacuationVolunteer['formData'],
  ): LocalEvacuationVolunteer {
    const now = new Date().toISOString();
    const vol: LocalEvacuationVolunteer = {
      id: generateId('VEVC'),
      type: 'evacuation_volunteer',
      status: 'pending',
      syncStatus: 'local_only',
      formData: data,
      createdAt: now,
      updatedAt: now,
    };
    dispatch({ type: 'ADD_REQUEST', payload: vol });
    enqueueRequest(vol);
    return vol;
  }

  function addReliefVolunteer(
    data: LocalReliefVolunteer['formData'],
  ): LocalReliefVolunteer {
    const now = new Date().toISOString();
    const vol: LocalReliefVolunteer = {
      id: generateId('VREL'),
      type: 'relief_volunteer',
      status: 'pending',
      syncStatus: 'local_only',
      formData: data,
      createdAt: now,
      updatedAt: now,
    };
    dispatch({ type: 'ADD_REQUEST', payload: vol });
    enqueueRequest(vol);
    return vol;
  }

  function addReliefRequest(
    data: LocalReliefRequest['formData'],
  ): LocalReliefRequest {
    const now = new Date().toISOString();
    const req: LocalReliefRequest = {
      id: generateId('REL'),
      type: 'relief',
      status: 'pending',
      syncStatus: 'local_only',
      formData: data,
      createdAt: now,
      updatedAt: now,
    };
    dispatch({ type: 'ADD_REQUEST', payload: req });
    enqueueRequest(req);
    return req;
  }

  function addFieldReport(
    data: FieldReportFormData,
  ): LocalFieldReport {
    const now = new Date().toISOString();
    const req: LocalFieldReport = {
      id: generateId('FLD'),
      type: 'field_report',
      status: 'pending',
      syncStatus: 'local_only',
      formData: data,
      createdAt: now,
      updatedAt: now,
    };
    dispatch({ type: 'ADD_REQUEST', payload: req });
    enqueueRequest(req);
    return req;
  }

  function updateRequestStatus(id: string, status: RequestStatus) {
    dispatch({ type: 'UPDATE_STATUS', payload: { id, status } });
  }

  function deleteRequest(id: string) {
    dispatch({ type: 'DELETE_REQUEST', payload: { id } });
  }

  async function syncToBackend(request: LocalRequest): Promise<SyncResult> {
    updateSyncStatus(request.id, 'syncing');

    // Branch A: FieldReport dedicated endpoint submission
    if (request.type === 'field_report') {
      const fieldReport = request as LocalFieldReport;
      try {
        const result = await submitFieldReportApi(fieldReport.formData);
        if (result.success && result.data) {
          fieldReport.serverId = result.data.id;
          updateSyncStatus(request.id, 'server_confirmed');
          const queue = await loadQueue();
          const filtered = queue.filter((item) => item.requestId !== request.id);
          await saveQueue(filtered);
          return { local: true, backend: result as any, serverConfirmed: true };
        }
        updateSyncStatus(request.id, 'sync_failed');
        return { local: true, backend: result as any, serverConfirmed: false };
      } catch (err: any) {
        updateSyncStatus(request.id, 'sync_failed');
        return {
          local: true,
          backend: {
            data: null,
            error: { message: err?.message || 'Backend unavailable', code: 'BACKEND_UNAVAILABLE' },
            success: false,
          },
          serverConfirmed: false,
        };
      }
    }

    // Branch B: Standard incident batch sync
    const operation = createIncidentReportOperation(request);
    const batch = createSyncBatch([operation]);

    try {
      const result = await syncIncidents(batch);

      if (result.success && result.data) {
        const accepted = result.data.failed_ids.indexOf(request.id) === -1;
        updateSyncStatus(request.id, accepted ? 'server_confirmed' : 'sync_failed');

        if (accepted) {
          const queue = await loadQueue();
          const filtered = queue.filter((item) => item.requestId !== request.id);
          await saveQueue(filtered);
        }

        return { local: true, backend: result, serverConfirmed: accepted };
      }

      updateSyncStatus(request.id, 'sync_failed');
      return { local: true, backend: result, serverConfirmed: false };
    } catch {
      updateSyncStatus(request.id, 'sync_failed');
      return {
        local: true,
        backend: {
          data: null,
          error: { message: 'Backend unavailable', code: 'BACKEND_UNAVAILABLE' },
          success: false,
        },
        serverConfirmed: false,
      };
    }
  }

  return {
    requests: state.requests,
    volunteers: state.volunteers,
    allItems: [...state.requests],
    addEvacuationRequest,
    addHelpRequest,
    addReliefRequest,
    addFieldReport,
    addEvacuationVolunteer,
    addReliefVolunteer,
    updateRequestStatus,
    updateSyncStatus,
    deleteRequest,
    syncToBackend,
  };
}
