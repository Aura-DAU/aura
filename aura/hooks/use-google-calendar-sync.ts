"use client"

import { useCallback, useEffect, useState } from "react"

export type CalendarSyncStatus = "loading" | "not_connected" | "connected" | "syncing"

interface SyncResult {
  created?: number
  updated?: number
  removed?: number
  errors?: string[]
}

/**
 * Manages "sync my timetable to Google Calendar": connecting the student's
 * Google account with write access (calendar.events), triggering a sync of
 * their current timetable into recurring weekly events, and disconnecting.
 *
 * Reminder delivery for these events is entirely Google Calendar's job —
 * it already has notification support on desktop, laptop, Android, and
 * iOS, so there's no service-worker/push plumbing needed here (contrast
 * with use-push-notifications.ts, AURA's own separate reminder channel).
 */
export function useGoogleCalendarSync() {
  const [status, setStatus] = useState<CalendarSyncStatus>("loading")
  const [lastSync, setLastSync] = useState<SyncResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [justConnected, setJustConnected] = useState(false)

  const checkStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/calendar/status", { cache: "no-store" })
      if (!res.ok) {
        setStatus("not_connected")
        return
      }
      const data = await res.json()
      // Bug 10 fix: for faculty, the response has no can_sync_timetable field
      // (it's student-only). Fall back to the generic `linked` flag so faculty
      // correctly shows "connected" after linking their calendar.
      const canUse = "can_sync_timetable" in data ? data.can_sync_timetable : data.linked
      setStatus(canUse ? "connected" : "not_connected")
    } catch {
      setStatus("not_connected")
    }
  }, [])

  useEffect(() => {
    // The OAuth callback (server/api/routes/calendar_routes.py) redirects
    // back to /dashboard?calendar=connected once the student grants access.
    // Pick that up once, then strip it from the URL so a refresh doesn't
    // re-trigger it.
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search)
      if (params.get("calendar") === "connected") {
        setJustConnected(true)
        params.delete("calendar")
        const newSearch = params.toString()
        window.history.replaceState({}, "", window.location.pathname + (newSearch ? `?${newSearch}` : ""))
      }
    }
    checkStatus()
  }, [checkStatus])

  const connect = useCallback(async () => {
    setError(null)
    try {
      const res = await fetch("/api/calendar/connect", { cache: "no-store" })
      const data = await res.json()
      if (!res.ok || !data.url) {
        setError(data.detail || data.error || "Could not start Google Calendar connection.")
        return
      }
      // Full-page navigation to Google's consent screen — the OAuth
      // callback redirects back to /dashboard?calendar=connected when done.
      window.location.href = data.url
    } catch {
      setError("Network error while starting the Google Calendar connection.")
    }
  }, [])

  const sync = useCallback(async () => {
    setStatus("syncing")
    setError(null)
    try {
      const res = await fetch("/api/calendar/timetable/sync", { method: "POST" })
      const data = await res.json()
      if (!res.ok) {
        // Bug 2 fix: FastAPI HTTPException serialises to {detail: "..."},
        // not {error: "..."}. Read detail first, fall back to error for
        // non-FastAPI error shapes.
        setError(data.detail || data.error || "Failed to sync your timetable.")
        setStatus("connected")
        return
      }
      setLastSync(data)
      setStatus("connected")
    } catch {
      setError("Network error while syncing your timetable.")
      setStatus("connected")
    }
  }, [])

  // Right after the OAuth connect flow finishes, automatically run the
  // first sync so the student doesn't have to click twice — connect, then
  // immediately see their classes land on their calendar.
  useEffect(() => {
    if (justConnected && status === "connected") {
      setJustConnected(false)
      sync()
    }
  }, [justConnected, status, sync])

  const disconnect = useCallback(async () => {
    setStatus("syncing")
    setError(null)
    try {
      await fetch("/api/calendar/disconnect", { method: "DELETE" })
      setLastSync(null)
      setStatus("not_connected")
    } catch {
      setError("Network error while disconnecting.")
      setStatus("connected")
    }
  }, [])

  return { status, lastSync, error, justConnected, connect, sync, disconnect }
}
