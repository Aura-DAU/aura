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
  // Memory/profile/calendar deletes and writes are mutating, per-identity
  // requests — a stale/cached response here can make a successful delete
  // look like it failed (or vice versa). Always hit the network directly.
  "/api/memory",
  "/api/profile",
  "/api/push",
  "/api/calendar",
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

// eslint-disable-next-line @typescript-eslint/no-explicit-any
self.addEventListener("push", (event: any) => {
  let data = { title: "AURA", body: "You have a class coming up.", url: "/dashboard" }
  try {
    if (event.data) {
      data = { ...data, ...event.data.json() }
    }
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  } catch (err) {
    // Non-JSON push payload — fall back to defaults above.
  }

  event.waitUntil(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (self as any).registration.showNotification(data.title, {
      body: data.body,
      icon: "/icon-light-32x32.png",
      badge: "/icon-light-32x32.png",
      data: { url: data.url || "/dashboard" },
      tag: "aura-timetable-reminder",
    })
  )
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any
self.addEventListener("notificationclick", (event: any) => {
  event.notification.close()
  const url = (event.notification.data && event.notification.data.url) || "/dashboard"

  event.waitUntil(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (self as any).clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList: any[]) => {
      for (const client of clientList) {
        if (client.url.includes(url) && "focus" in client) {
          return client.focus()
        }
      }
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      if ((self as any).clients.openWindow) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        return (self as any).clients.openWindow(url)
      }
    })
  )
})

serwist.addEventListeners()
