import { defaultCache } from "@serwist/next/worker"
import type { PrecacheEntry, RuntimeCaching, SerwistGlobalConfig } from "serwist"
import { NetworkOnly, Serwist } from "serwist"

declare global {
  interface WorkerGlobalScope extends SerwistGlobalConfig {
    __SW_MANIFEST: (PrecacheEntry | string)[] | undefined
  }
}

declare const self: WorkerGlobalScope

// Serwist's defaultCache NetworkFirst-caches every same-origin GET to /api/*
// (the "apis" rule). These routes return authenticated/personal data, so they
// must never be cached — always hit the network and never serve a stale copy.
// Matched before defaultCache so this rule wins.
const SENSITIVE_API_PREFIXES = [
  "/api/auth",
  "/api/chat",
  "/api/timetable",
  "/api/ecampus",
  "/api/admin",
  "/api/documents",
  "/api/speech",
]

const runtimeCaching: RuntimeCaching[] = [
  {
    matcher: ({ url, sameOrigin }) =>
      sameOrigin && SENSITIVE_API_PREFIXES.some((prefix) => url.pathname.startsWith(prefix)),
    handler: new NetworkOnly(),
  },
  ...defaultCache,
]

const serwist = new Serwist({
  precacheEntries: self.__SW_MANIFEST,
  skipWaiting: true,
  clientsClaim: true,
  navigationPreload: true,
  runtimeCaching,
  fallbacks: {
    entries: [
      {
        url: "/offline",
        matcher({ request }: { request: Request }) {
          return request.destination === "document"
        },
      },
    ],
  },
})

serwist.addEventListeners()
