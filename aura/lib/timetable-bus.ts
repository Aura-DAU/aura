"use client"

/**
 * timetable-bus.ts — tiny same-origin pub/sub so that, the moment AURA's
 * chat pipeline applies a timetable/elective/cohort change (see
 * `chunk.type === "timetable-updated"` in use-aura-chat.ts), every open
 * timetable-consuming component — the dashboard's TimetableCard, the
 * StudentDashboard's embedded schedule, another browser tab entirely —
 * refetches right away instead of waiting for a window "focus" event.
 *
 * Uses BroadcastChannel where available (works across tabs of the same
 * origin, e.g. chat open in one tab and /dashboard open in another) and
 * falls back to a same-tab CustomEvent so it still works in browsers/test
 * environments without BroadcastChannel support.
 */

const CHANNEL_NAME = "aura-timetable-updates"
const EVENT_NAME = "aura:timetable-updated"

function getChannel(): BroadcastChannel | null {
  if (typeof window === "undefined" || typeof BroadcastChannel === "undefined") {
    return null
  }
  return new BroadcastChannel(CHANNEL_NAME)
}

/** Call this once the chat pipeline confirms a timetable-affecting change
 * was applied this turn. Notifies this tab immediately and any other
 * same-origin tab via BroadcastChannel. */
export function publishTimetableUpdated(): void {
  if (typeof window === "undefined") return

  // Same-tab listeners (e.g. this tab's own dashboard components).
  window.dispatchEvent(new CustomEvent(EVENT_NAME))

  // Other tabs.
  const channel = getChannel()
  if (channel) {
    try {
      channel.postMessage({ type: EVENT_NAME })
    } finally {
      channel.close()
    }
  }
}

/** Subscribe to timetable-updated notifications. Returns an unsubscribe
 * function — call it from a useEffect cleanup. */
export function subscribeTimetableUpdated(callback: () => void): () => void {
  if (typeof window === "undefined") {
    return () => {}
  }

  const onCustomEvent = () => callback()
  window.addEventListener(EVENT_NAME, onCustomEvent)

  const channel = getChannel()
  const onMessage = (event: MessageEvent) => {
    if (event?.data?.type === EVENT_NAME) callback()
  }
  channel?.addEventListener("message", onMessage)

  return () => {
    window.removeEventListener(EVENT_NAME, onCustomEvent)
    if (channel) {
      channel.removeEventListener("message", onMessage)
      channel.close()
    }
  }
}
