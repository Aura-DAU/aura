"use client"

import { useCallback, useEffect, useState } from "react"

export interface ElectiveSlot {
  master_id: string
  day: string
  day_of_week: number
  start_time: string
  end_time: string
  faculty_name: string
  room: string
}

export interface ElectiveCourse {
  course_code: string
  course_name: string
  course_type: string
  selected: boolean
  slots: ElectiveSlot[]
}

interface ElectivesResponse {
  cohort: { year: number; sem: number; sec: string }
  electives_configured: boolean
  electives: ElectiveCourse[]
}

export function useElectives() {
  const [data, setData] = useState<ElectivesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  const refetch = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/timetable/electives", { cache: "no-store" })
      const json = await res.json()
      if (!res.ok) {
        throw new Error(json?.detail || json?.error || "Failed to load electives")
      }
      setData(json)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load electives")
    } finally {
      setLoading(false)
    }
  }, [])

  const saveSelections = useCallback(async (courseCodes: string[]) => {
    setSaving(true)
    setError(null)
    try {
      const res = await fetch("/api/timetable/electives", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ course_codes: courseCodes }),
      })
      const json = await res.json()
      if (!res.ok) {
        throw new Error(json?.detail || json?.error || "Failed to save selections")
      }
      // Refetch to get updated selection status
      await refetch()
      return json
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save selections"
      setError(msg)
      throw err
    } finally {
      setSaving(false)
    }
  }, [refetch])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refetch()
  }, [refetch])

  return { data, loading, error, saving, refetch, saveSelections }
}
