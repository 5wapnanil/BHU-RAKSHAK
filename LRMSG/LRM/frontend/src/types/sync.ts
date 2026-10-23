export type NetworkStatus = 'ONLINE' | 'OFFLINE' | 'SYNCING' | 'ERROR';

export interface QueuedOperation {
  id: string;
  operationType: 'CREATE' | 'UPDATE' | 'DELETE' | 'POST' | 'PUT' | 'PATCH';
  entityType: string;
  payload: any;
  createdAt: number;
  status: 'PENDING' | 'SYNCING' | 'FAILED' | 'SYNCED';
  retryCount: number;
}
