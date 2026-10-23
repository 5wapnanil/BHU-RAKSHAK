// Foundational Service Worker for Offline Capabilities
const CACHE_NAME = 'lrmsg-offline-cache-v1';

self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installed');
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activated');
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  // Pass-through fetch handler for now. 
  // DO NOT AGGRESSIVELY CACHE yet (per Step 2F instructions).
  // This just establishes the service worker foundation.
});
