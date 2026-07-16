/// <reference lib="webworker" />

import { defaultCache } from "@serwist/next/worker"
import type { PrecacheEntry, SerwistGlobalConfig } from "serwist"
import { Serwist, NetworkFirst, StaleWhileRevalidate } from "serwist"

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined
  }
}

declare const self: ServiceWorkerGlobalScope

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching: [
    // Read-only ERP snapshots (fees/cgpa/timetable/registration) are safe to
    // serve stale-while-revalidate — this app never writes to these routes.
    {
      matcher: /\/api\/erp\/.*/,
      handler: new StaleWhileRevalidate({ cacheName: "erp-snapshots" }),
    },
    // Chat is never cached — always network, so a stale answer is never
    // served as if it were current. If offline, this simply fails and the
    // UI's own error state handles it (no cached chat responses exist).
    {
      matcher: /\/api\/chat.*/,
      handler: new NetworkFirst({ cacheName: "chat", networkTimeoutSeconds: 10 }),
    },
    ...defaultCache,
  ],
  fallbacks: {
    entries: [
      {
        url: "/offline",
        matcher: ({ request }) => request.destination === "document",
      },
    ],
  },
})

serwist.addEventListeners()
