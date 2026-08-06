"use client"

import { useCallback, useEffect, useState } from "react"

export interface CohortYearOption {
  year: number
  semesters: number[]
  sections: string[]
}

export interface CohortProgramOption {
  program: string
  branches: string[]
  years: CohortYearOption[]
}

export interface CohortOptions {
  options: CohortProgramOption[]
}

export interface CohortProfile {
  erp_id: string
  current_year: number | null
  current_sem: number | null
  current_sec: string | null
  is_configured: boolean
}

export interface SaveCohortRequest {
  program: string
  year: number
  semester: number
  section: string
  branch?: string
}

export function useCohortProfile() {
  const [profile, setProfile] = useState<CohortProfile | null>(null)
  const [options, setOptions] = useState<CohortProgramOption[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchProfile = useCallback(async (signal?: AbortSignal) => {
    try {
      const res = await fetch("/api/profile/cohort", {
        cache: "no-store",
        signal,
      })
      if (res.ok) {
        setProfile(await res.json())
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return
      // Non-fatal: profile might not be accessible yet
    }
  }, [])

  const fetchOptions = useCallback(async (signal?: AbortSignal) => {
    try {
      const res = await fetch("/api/profile/cohort-options", {
        cache: "no-store",
        signal,
      })
      if (res.ok) {
        const data = await res.json()
        setOptions(data.options || [])
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return
      // Non-fatal
    }
  }, [])

  const saveCohort = useCallback(async (data: SaveCohortRequest) => {
    setSaving(true)
    setError(null)
    try {
      const res = await fetch("/api/profile/cohort", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
      const json = await res.json()
      if (!res.ok) {
        throw new Error(json?.detail || json?.error || "Failed to save profile")
      }
      await fetchProfile()
      return json
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to save profile"
      setError(msg)
      throw err
    } finally {
      setSaving(false)
    }
  }, [fetchProfile])

  useEffect(() => {
    const controller = new AbortController()
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoading(true)
    Promise.all([
      fetchProfile(controller.signal),
      fetchOptions(controller.signal),
    ]).finally(() => {
      if (!controller.signal.aborted) setLoading(false)
    })
    return () => controller.abort()
  }, [fetchProfile, fetchOptions])

  return { profile, options, loading, saving, error, saveCohort, refetch: fetchProfile }
}
