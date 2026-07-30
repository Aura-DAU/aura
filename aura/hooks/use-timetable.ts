"use client"

import { useCallback, useEffect, useState } from "react"

export interface TimetableSlot {
  id: string
  day_of_week: number
  day: string
  start_time: string
  end_time: string
  course_code: string
  course_name: string
  session_type: "lecture" | "lab" | "tutorial"
  room?: string | null
  faculty_name?: string | null
  is_custom: boolean
}

interface TimetableResponse {
  cohort: { year: number; sem: number; sec: string }
  timetable: TimetableSlot[]
}

export function useTimetable() {
  const [data, setData] = useState<TimetableResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    const controller = new AbortController()
    try {
      const res = await fetch("/api/timetable/me", {
        cache: "no-store",
        signal: controller.signal,
      })
      if (!res.ok) {
        // Safely parse JSON error body — fall back if it isn't JSON (e.g. nginx 502 HTML)
        let msg = "Failed to load timetable"
        try {
          const errJson = await res.json()
          if (errJson?.error) msg = errJson.error
        } catch {
          // non-JSON body — keep the default message
        }
        throw new Error(msg)
      }
      const json = await res.json()
      setData(json)
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") return
      setError(err instanceof Error ? err.message : "Failed to load timetable")
    } finally {
      setLoading(false)
    }
    return () => controller.abort()
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refetch()

    // The agent can change the timetable mid-conversation (in another tab
    // or the chat panel). Re-fetching on window focus keeps the dashboard
    // card showing the latest version without needing a websocket.
    const onFocus = () => refetch()
    window.addEventListener("focus", onFocus)
    return () => window.removeEventListener("focus", onFocus)
  }, [refetch])

  return { data, loading, error, refetch }
}
