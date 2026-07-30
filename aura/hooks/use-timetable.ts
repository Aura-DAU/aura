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
    try {
      const res = await fetch("/api/timetable/me", { cache: "no-store" })
      const json = await res.json()
      if (!res.ok) {
        throw new Error(json?.error || "Failed to load timetable")
      }
      setData(json)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load timetable")
    } finally {
      setLoading(false)
    }
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
