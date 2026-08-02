"use client"

import { useEffect, useState } from "react"

type CalendarSyncResponseState = "idle" | "syncing" | "completed" | "failed"

export type TimetableSyncState = Exclude<CalendarSyncResponseState, "idle">

export interface TimetableSyncStatus {
  state: TimetableSyncState
  created: number
  updated: number
  removed: number
  hasWarnings: boolean
}

const INITIAL_STATUS: TimetableSyncStatus = {
  state: "syncing",
  created: 0,
  updated: 0,
  removed: 0,
  hasWarnings: false,
}

const POLL_INTERVAL_MS = 1500
const MAX_STATUS_FAILURES = 3
const MAX_IDLE_POLLS = 5

interface CalendarSyncResponse extends Omit<TimetableSyncStatus, "state"> {
  state: CalendarSyncResponseState
}

function isSyncStatus(value: unknown): value is CalendarSyncResponse {
  if (!value || typeof value !== "object") return false
  const candidate = value as Partial<CalendarSyncResponse>
  return (
    (candidate.state === "idle" ||
      candidate.state === "syncing" ||
      candidate.state === "completed" ||
      candidate.state === "failed") &&
    typeof candidate.created === "number" &&
    typeof candidate.updated === "number" &&
    typeof candidate.removed === "number" &&
    typeof candidate.hasWarnings === "boolean"
  )
}

export function useCalendarSyncStatus(): TimetableSyncStatus {
  const [status, setStatus] = useState<TimetableSyncStatus>(INITIAL_STATUS)

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    let failedPolls = 0
    let idlePolls = 0

    const poll = async () => {
      try {
        const response = await fetch("/api/calendar/timetable/sync", {
          cache: "no-store",
          signal: controller.signal,
        })
        if (!response.ok) throw new Error("Calendar sync status request failed")

        const data: unknown = await response.json()
        if (!isSyncStatus(data)) throw new Error("Invalid calendar sync status")
        failedPolls = 0

        if (data.state === "idle") {
          idlePolls += 1
          if (idlePolls >= MAX_IDLE_POLLS) {
            setStatus({ ...INITIAL_STATUS, state: "failed" })
            return
          }
          timer = setTimeout(poll, POLL_INTERVAL_MS)
          return
        }

        if (data.state === "syncing") {
          idlePolls = 0
          setStatus({ ...data, state: "syncing" })
          timer = setTimeout(poll, POLL_INTERVAL_MS)
          return
        }

        if (data.state === "completed") {
          setStatus({ ...data, state: "completed" })
          return
        }

        setStatus({ ...data, state: "failed" })
      } catch {
        if (!controller.signal.aborted) {
          failedPolls += 1
          if (failedPolls >= MAX_STATUS_FAILURES) {
            setStatus({ ...INITIAL_STATUS, state: "failed" })
            return
          }
          timer = setTimeout(poll, POLL_INTERVAL_MS)
        }
      }
    }

    void poll()

    return () => {
      controller.abort()
      if (timer) clearTimeout(timer)
    }
  }, [])

  return status
}
