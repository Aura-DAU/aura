// AURA service worker — currently scoped to one job: showing the
// "class starts in 10 minutes" push notification sent by the backend
// scheduler (server/rag/pipeline/timetable/notifier.py).

// eslint-disable-next-line @typescript-eslint/no-unused-vars
self.addEventListener("install", (event) => {
  self.skipWaiting()
})

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim())
})

self.addEventListener("push", (event) => {
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
    self.registration.showNotification(data.title, {
      body: data.body,
      icon: "/icon-light-32x32.png",
      badge: "/icon-light-32x32.png",
      data: { url: data.url || "/dashboard" },
      tag: "aura-timetable-reminder",
    })
  )
})

self.addEventListener("notificationclick", (event) => {
  event.notification.close()
  const url = (event.notification.data && event.notification.data.url) || "/dashboard"

  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (client.url.includes(url) && "focus" in client) {
          return client.focus()
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(url)
      }
    })
  )
})
