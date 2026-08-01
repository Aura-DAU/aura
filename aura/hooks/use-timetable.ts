"use client"

import { useCallback, useEffect, useRef, useState } from "react"

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
  // Used to split the grid into the core weekly table vs. the ELECTIVE
  // band underneath it (see service._is_elective on the backend).
  course_type?: string | null
}

interface TimetableResponse {
  cohort: { year: number; sem: number; sec: string }
  timetable: TimetableSlot[]
  // True when the backend couldn't find this student's own configured
  // section yet and fell back to the shared default timetable for their
  // inferred year (section "A"). See service.get_effective_timetable.
  is_common?: boolean
  // True when is_common, OR the student hasn't picked their electives yet.
  // Used to show the "personalize in chat" nudge without blocking the view.
  needs_configuration?: boolean
  electives_configured?: boolean
}

export function useTimetable() {
  const [data, setData] = useState<TimetableResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  // BUG-07 fix: `refetch` used to create its own AbortController and
  // `return () => controller.abort()` — but since refetch is an async
  // function called as `refetch()` (not awaited/returned) inside the
  // effect, that cleanup closure was just the resolved value of a
  // discarded Promise. It was never invoked, so in-flight requests were
  // never aborted on unmount or when a newer refetch superseded them.
  // Tracking the controller in a ref lets both the effect's cleanup AND
  // a fresh refetch() call reach and abort the actual in-flight request.
  const controllerRef = useRef<AbortController | null>(null)

  const refetch = useCallback(async () => {
    controllerRef.current?.abort()
    const controller = new AbortController()
    controllerRef.current = controller

    setLoading(true)
    setError(null)
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
  }, [])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refetch()

    // The agent can change the timetable mid-conversation (in another tab
    // or the chat panel). Re-fetching on window focus keeps the dashboard
    // card showing the latest version without needing a websocket.
    const onFocus = () => refetch()
    window.addEventListener("focus", onFocus)
    return () => {
      window.removeEventListener("focus", onFocus)
      controllerRef.current?.abort()
    }
  }, [refetch])

  return { data, loading, error, refetch }
}
