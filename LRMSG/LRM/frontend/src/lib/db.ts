import { openDB, DBSchema, IDBPDatabase } from 'idb';
import { QueuedOperation } from '@/types/sync';

interface AppDB extends DBSchema {
  alerts: {
    key: string;
    value: any;
  };
  gis_cache: {
    key: string;
    value: any;
  };
  prediction_cache: {
    key: string;
    value: any;
  };
  pending_sync: {
    key: string;
    value: QueuedOperation;
    indexes: { 'by-status': string };
  };
  test_store: {
    key: string;
    value: any;
  };
}

const DB_NAME = 'lrmsg-offline-db';
const DB_VERSION = 2;

let dbPromise: Promise<IDBPDatabase<AppDB>> | null = null;

export const getDB = () => {
  if (typeof window === 'undefined') return null;
  
  if (!dbPromise) {
    dbPromise = openDB<AppDB>(DB_NAME, DB_VERSION, {
      upgrade(db, oldVersion, newVersion, transaction) {
        if (!db.objectStoreNames.contains('alerts')) {
          db.createObjectStore('alerts', { keyPath: 'id' });
        } else if (oldVersion < 2 && !db.objectStoreNames.contains('alerts')) {
           // handled
        }
        if (!db.objectStoreNames.contains('gis_cache')) {
          db.createObjectStore('gis_cache');
        }
        if (!db.objectStoreNames.contains('prediction_cache')) {
          db.createObjectStore('prediction_cache');
        }
        if (!db.objectStoreNames.contains('pending_sync')) {
          const syncStore = db.createObjectStore('pending_sync', { keyPath: 'id' });
          syncStore.createIndex('by-status', 'status');
        }
        if (!db.objectStoreNames.contains('test_store')) {
          db.createObjectStore('test_store', { keyPath: 'id' });
        }
      },
    });
  }
  return dbPromise;
};

// --- HELPER FUNCTIONS FOR CACHING ---

export const saveAlertsToCache = async (alerts: any[]) => {
  const db = await getDB();
  if (!db) return;
  const tx = db.transaction('alerts', 'readwrite');
  await tx.objectStore('alerts').clear();
  for (const alert of alerts) {
    // Inject cached metadata
    const toSave = { ...alert, cachedAt: Date.now() };
    await tx.objectStore('alerts').put(toSave);
  }
  await tx.done;
};

export const getCachedAlerts = async () => {
  const db = await getDB();
  if (!db) return [];
  return await db.getAll('alerts');
};

export const saveGISDataToCache = async (key: string, data: any) => {
  const db = await getDB();
  if (!db) return;
  await db.put('gis_cache', { data, cachedAt: Date.now() }, key);
};

export const getCachedGISData = async (key: string) => {
  const db = await getDB();
  if (!db) return null;
  return await db.get('gis_cache', key);
};

export const savePredictionToCache = async (key: string, data: any) => {
  const db = await getDB();
  if (!db) return;
  await db.put('prediction_cache', { data, cachedAt: Date.now() }, key);
};

export const getCachedPrediction = async (key: string) => {
  const db = await getDB();
  if (!db) return null;
  return await db.get('prediction_cache', key);
};


