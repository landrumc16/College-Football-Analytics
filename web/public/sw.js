/* Minimal shell worker. Live JSON is always network-only, never cached. */
const SHELL_CACHE = 'cfb-shell-v341';
self.addEventListener('install', event => { event.waitUntil(caches.open(SHELL_CACHE).then(cache => cache.add(new URL('offline.html', self.registration.scope).href))); self.skipWaiting(); });
self.addEventListener('activate', event => { event.waitUntil((async () => { const keys = await caches.keys(); await Promise.all(keys.filter(k => k.startsWith('cfb-shell-') && k !== SHELL_CACHE).map(k => caches.delete(k))); await self.clients.claim(); })()); });
self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== self.location.origin) return;
  const url = new URL(req.url);
  // Navigation and all data requests must reach the network. A missing connection
  // yields a clear failure rather than silently showing obsolete football results.
  if (req.mode === 'navigate' || !url.pathname.includes('/assets/') || !/\.[a-f0-9]{8,}\.(js|css)$/.test(url.pathname)) return;
  event.respondWith(caches.open(SHELL_CACHE).then(async cache => {
    const hit = await cache.match(req);
    if (hit) return hit;
    const response = await fetch(req);
    if (response.ok) await cache.put(req, response.clone());
    return response;
  }));
});
