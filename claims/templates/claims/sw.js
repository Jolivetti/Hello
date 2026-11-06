const CACHE_NAME = 'legalcrm-v1';
const PRECACHE_ASSETS = [
  '/login/',
  '/static/claims/laurel_crest.png',
  '/static/claims/olivetti_group.png',
  '/static/claims/lady_justice.jpg'
];

// Install: Cache critical static assets and login shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_ASSETS))
  );
  self.skipWaiting();
});

// Activate: Purge obsolete cache stores
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      )
    )
  );
  self.clients.claim();
});

// Fetch: Network-first strategy with cache fallback
self.addEventListener('fetch', (event) => {
  // Only handle GET requests; pass POST/auth requests straight to the network
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
});