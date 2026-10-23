"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { processSyncQueue, getPendingOperations } from '@/lib/syncManager';

interface NetworkContextType {
  isOnline: boolean;
  pendingCount: number;
  failedCount: number;
  isSyncingState: boolean;
  syncNow: () => void;
}

const NetworkContext = createContext<NetworkContextType>({
  isOnline: true,
  pendingCount: 0,
  failedCount: 0,
  isSyncingState: false,
  syncNow: () => {}
});

export const NetworkProvider = ({ children }: { children: ReactNode }) => {
  const [isOnline, setIsOnline] = useState<boolean>(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [failedCount, setFailedCount] = useState(0);
  const [isSyncingState, setIsSyncingState] = useState(false);

  const fetchSyncStatus = async () => {
    try {
      const ops = await getPendingOperations();
      const syncing = ops.some(o => o.status === 'SYNCING');
      const failed = ops.filter(o => o.status === 'FAILED').length;
      const pending = ops.filter(o => o.status === 'PENDING').length;
      
      setPendingCount(pending);
      setFailedCount(failed);
      setIsSyncingState(syncing);
    } catch (err) {
      console.warn("Failed to check pending sync count");
    }
  };

  const syncNow = () => {
    if (isOnline) {
      processSyncQueue();
    }
  };

  useEffect(() => {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(err => console.log('SW registration failed:', err));
    }

    setIsOnline(navigator.onLine);
    fetchSyncStatus();
    if (navigator.onLine) {
      processSyncQueue();
    }

    const handleOnline = () => {
      setIsOnline(true);
      processSyncQueue();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    window.addEventListener('sync-status-change', fetchSyncStatus);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      window.removeEventListener('sync-status-change', fetchSyncStatus);
    };
  }, []);

  return (
    <NetworkContext.Provider value={{ isOnline, pendingCount, failedCount, isSyncingState, syncNow }}>
      {children}
    </NetworkContext.Provider>
  );
};

export const useNetworkStatus = () => useContext(NetworkContext);
