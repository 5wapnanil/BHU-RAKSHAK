import { useState, useEffect, useCallback } from 'react';
import {
  checkConnectivity,
  subscribeToNetworkChanges,
} from '../services/connectivity';
import type { ConnectivityStatus } from '../services/connectivity';

export interface UseConnectivityResult {
  status: ConnectivityStatus;
  isOnline: boolean;
  isOffline: boolean;
  backendAvailable: boolean;
  checkConnectivity: () => Promise<ConnectivityStatus>;
}

export function useConnectivity(): UseConnectivityResult {
  const [status, setStatus] = useState<ConnectivityStatus>('checking');

  const refresh = useCallback(async (): Promise<ConnectivityStatus> => {
    const result = await checkConnectivity();
    setStatus(result);
    return result;
  }, []);

  useEffect(() => {
    refresh();

    const unsubscribe = subscribeToNetworkChanges(async (isConnected) => {
      if (!isConnected) {
        setStatus('offline');
      } else {
        const result = await checkConnectivity();
        setStatus(result);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [refresh]);

  return {
    status,
    isOnline: status === 'online',
    isOffline: status === 'offline',
    backendAvailable: status === 'online',
    checkConnectivity: refresh,
  };
}
