"use client"

import { AlertTriangle, CalendarCheck, Check, Loader2 } from "lucide-react"

import { useCalendarSyncStatus } from "@/hooks/use-calendar-sync-status"

interface TimetableSyncCardProps {
  eventCount?: number
}

export function TimetableSyncCard({ eventCount }: TimetableSyncCardProps) {
  const status = useCalendarSyncStatus()

  if (status.state === "completed") {
    return (
      <div className="rounded-xl border border-green-500/20 bg-green-500/5 p-4 animate-in fade-in slide-in-from-bottom-1 duration-300">
        <div className="flex items-start gap-2.5">
          <Check className="mt-0.5 size-4 shrink-0 text-green-400" />
          <div>
            <p className="text-sm font-semibold text-neutral-100">Timetable synced</p>
            <p className="mt-0.5 text-xs text-neutral-400">
              {status.created} created · {status.updated} updated · {status.removed} removed
            </p>
            {status.hasWarnings ? (
              <p className="mt-1 text-xs text-theme-yellow">
                Some events need another sync attempt.
              </p>
            ) : null}
          </div>
        </div>
      </div>
    )
  }

  if (status.state === "failed") {
    return (
      <div className="rounded-xl border border-theme-red/20 bg-theme-red/5 p-4 animate-in fade-in slide-in-from-bottom-1 duration-300">
        <div className="flex items-start gap-2.5">
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-theme-red" />
          <div>
            <p className="text-sm font-semibold text-neutral-100">Calendar sync couldn&apos;t finish</p>
            <p className="mt-0.5 text-xs text-neutral-400">Please try syncing again.</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div
      role="status"
      className="rounded-xl border border-theme-yellow/20 bg-theme-yellow/5 p-4 animate-in fade-in slide-in-from-bottom-1 duration-300"
    >
      <div className="flex items-start gap-2.5">
        <Loader2 className="mt-0.5 size-4 shrink-0 animate-spin text-theme-yellow" />
        <div>
          <p className="text-sm font-semibold text-neutral-100">Syncing timetable…</p>
          <p className="mt-0.5 text-xs text-neutral-400">
            {eventCount
              ? `Adding ${eventCount} recurring class events to Google Calendar.`
              : "Adding your recurring class events to Google Calendar."}
          </p>
          <p className="mt-1 inline-flex items-center gap-1 text-xs text-neutral-500">
            <CalendarCheck className="size-3" /> You can keep chatting while this finishes.
          </p>
        </div>
      </div>
    </div>
  )
}
