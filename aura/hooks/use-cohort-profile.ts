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

  const fetchProfile = useCallback(async () => {
    try {
      const res = await fetch("/api/profile/cohort", { cache: "no-store" })
      if (res.ok) {
        setProfile(await res.json())
      }
    } catch {
      // Non-fatal: profile might not be accessible yet
    }
  }, [])

  const fetchOptions = useCallback(async () => {
    try {
      const res = await fetch("/api/profile/cohort-options", { cache: "no-store" })
      if (res.ok) {
        const data = await res.json()
        setOptions(data.options || [])
      }
    } catch {
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
      // Refresh profile after save
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
    setLoading(true)
    Promise.all([fetchProfile(), fetchOptions()]).finally(() => setLoading(false))
  }, [fetchProfile, fetchOptions])

  return { profile, options, loading, saving, error, saveCohort, refetch: fetchProfile }
}
