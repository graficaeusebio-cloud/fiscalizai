// ══════════════════════════════════════
//  FISCALIZAÍ — Service Worker
//  Cache-first para assets, network-first para API
// ══════════════════════════════════════

const CACHE_NAME = 'fiscalizai-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json'
];

// ── Install: cacheia assets estáticos ──
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ── Activate: limpa caches antigas ──
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// ── Fetch: estratégia por tipo ──
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // API do Portal da Transparência → network-first, fallback cache
  if (url.hostname.includes('portaldatransparencia') || url.hostname.includes('corsproxy')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          if (response.ok) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }

  // Assets estáticos → cache-first
  if (url.pathname.match(/\.(html|js|css|png|svg|ico|woff2?)$/)) {
    event.respondWith(
      caches.match(event.request).then(cached => cached || fetch(event.request))
    );
    return;
  }

  // Google Fonts → stale-while-revalidate
  if (url.hostname.includes('fonts.googleapis') || url.hostname.includes('fonts.gstatic')) {
    event.respondWith(
      caches.open(CACHE_NAME).then(async cache => {
        const cached = await cache.match(event.request);
        const fresh = fetch(event.request).then(res => {
          if (res.ok) cache.put(event.request, res.clone());
          return res;
        }).catch(() => cached);
        return cached || fresh;
      })
    );
    return;
  }

  // Default: network com fallback
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
