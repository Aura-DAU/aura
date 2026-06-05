const CACHE_NAME = "dau-pwa-cache-v1";
const ASSETS_TO_CACHE = [
  "/",
  "/offline.html",
  "/favicon.ico",
  "/icons/icon-192x192.png",
  "/icons/icon-512x512.png",
  "/icons/icon-512x512-maskable.png",
];

// Install Event
self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

// Activate Event
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Event
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);

  // Avoid intercepting third-party requests or hot-reloading web sockets
  if (url.origin !== self.location.origin) return;
  if (url.pathname.includes("webpack")) return;
  if (url.pathname.startsWith("/api/")) return;

  // Explicit caching allowlist
  const isNextStatic = url.pathname.startsWith("/_next/static/");
  const isIcon = url.pathname.startsWith("/icons/") || url.pathname === "/favicon.ico";
  const isLogo = url.pathname.match(/^\/dau_logo\.(png|jpg|jpeg|webp|svg)/i);
  const isManifest = url.pathname.endsWith(".webmanifest") || url.pathname.endsWith(".json");
  const isCacheableAsset = ASSETS_TO_CACHE.includes(url.pathname);

  const shouldCache = isNextStatic || isIcon || isLogo || isManifest || isCacheableAsset;

  if (shouldCache) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          // Serve from cache, but fetch in background to refresh the cache
          fetch(event.request)
            .then((response) => {
              if (response && response.status === 200 && response.type === "basic") {
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(event.request, response);
                });
              }
            })
            .catch(() => {});
          return cachedResponse;
        }

        return fetch(event.request)
          .then((response) => {
            if (response && response.status === 200 && response.type === "basic") {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseToCache);
              });
            }
            return response;
          })
          .catch(() => caches.match(event.request));
      })
    );
  } else {
    // Network-only with cache/fallback fallback (e.g., for HTML pages when offline)
    event.respondWith(
      fetch(event.request).catch(() => {
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            return cachedResponse;
          }
          if (event.request.headers.get("accept")?.includes("text/html")) {
            return caches.match("/offline.html");
          }
        });
      })
    );
  }
});
