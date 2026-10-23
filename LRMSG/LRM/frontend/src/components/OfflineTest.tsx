"use client";

import React, { useEffect, useState } from 'react';
import { getDB } from '@/lib/db';
import { useNetworkStatus } from '@/contexts/NetworkContext';

export default function OfflineTest() {
  const { isOnline } = useNetworkStatus();
  const [dbStatus, setDbStatus] = useState<string>("Initializing...");
  const [storedRecord, setStoredRecord] = useState<any>(null);

  useEffect(() => {
    const testDB = async () => {
      try {
        const db = await getDB();
        if (!db) {
          setDbStatus("No DB support (SSR)");
          return;
        }
        
        // 1. Write a record
        const testId = "test-record-1";
        const payload = { id: testId, timestamp: Date.now(), message: "IndexedDB works!" };
        await db.put('test_store', payload);
        
        // 2. Read it back
        const result = await db.get('test_store', testId);
        if (result) {
          setStoredRecord(result);
          setDbStatus("IndexedDB is successfully storing records.");
        } else {
          setDbStatus("Failed to read test record.");
        }
      } catch (err: any) {
        setDbStatus(`Error testing IndexedDB: ${err.message}`);
      }
    };

    testDB();
  }, []);

  return (
    <div style={{
      position: 'fixed',
      bottom: '10px',
      left: '10px',
      padding: '12px',
      background: 'rgba(0,0,0,0.85)',
      color: '#fff',
      borderRadius: '8px',
      fontSize: '12px',
      fontFamily: 'monospace',
      zIndex: 9999,
      maxWidth: '300px'
    }}>
      <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: isOnline ? '#22c55e' : '#ef4444' }} />
        <strong>Network: {isOnline ? 'ONLINE' : 'OFFLINE'}</strong>
      </div>
      <div style={{ color: '#aaa' }}>{dbStatus}</div>
      {storedRecord && (
        <div style={{ marginTop: '4px', color: '#6ee7b7' }}>
          Latest read: {storedRecord.message}
        </div>
      )}
    </div>
  );
}
