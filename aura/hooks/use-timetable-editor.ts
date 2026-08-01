"use client"

import { useCallback, useState } from "react"

export interface TimetableChangeInput {
  kind: "replace" | "add" | "remove"
  day?: string
  start_time?: string
  end_time?: string
  course_code?: string
  course_name?: string
  session_type?: "lecture" | "lab" | "tutorial"
  room?: string
  faculty_name?: string
  note?: string
}

interface CalendarSyncResult {
  status: string
  created?: number
  updated?: number
  removed?: number
  message?: string
}

/**
 * Dashboard-side timetable editing: add a new class, replace/move an
 * existing one, remove one, or undo a previous personal change. Mirrors
 * the chat agent's update_my_timetable / undo_timetable_change tools, but
 * calls straight through (no confirm-preview round trip) since submitting
 * the dashboard form already is the confirmation — see
 * server/api/routes/timetable_routes.py for the shared reasoning.
 *
 * The backend refreshes Google Calendar automatically after every change
 * (only if the student already linked it with write access), and returns
 * that result as `calendar_sync` on the response — surfaced here so the
 * card can show a quiet "synced" hint without a separate manual step.
 */
export function useTimetableEditor() {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastCalendarSync, setLastCalendarSync] = useState<CalendarSyncResult | null>(null)

  const applyChange = useCallback(async (change: TimetableChangeInput) => {
    setSaving(true)
    setError(null)
    try {
      const res = await fetch("/api/timetable/changes", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(change),
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data?.error || data?.detail || "Failed to save the timetable change.")
      }
      if (data?.calendar_sync) setLastCalendarSync(data.calendar_sync)
      return data
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save the timetable change."
      setError(msg)
      throw err
    } finally {
      setSaving(false)
    }
  }, [])

  const removeChange = useCallback(async (overrideId: string) => {
    setSaving(true)
    setError(null)
    try {
      const res = await fetch(`/api/timetable/changes/${encodeURIComponent(overrideId)}`, {
        method: "DELETE",
      })
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data?.error || data?.detail || "Failed to remove that timetable change.")
      }
      if (data?.calendar_sync) setLastCalendarSync(data.calendar_sync)
      return data
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to remove that timetable change."
      setError(msg)
      throw err
    } finally {
      setSaving(false)
    }
  }, [])

  return { saving, error, lastCalendarSync, applyChange, removeChange, clearError: () => setError(null) }
}
