"use client"

import { CalendarCheck } from "lucide-react"

interface TimetableSyncConfirmationCardProps {
  eventCount?: number
  onConfirm?: () => void
}

export function TimetableSyncConfirmationCard({
  eventCount,
  onConfirm,
}: TimetableSyncConfirmationCardProps) {
  return (
    <div className="rounded-xl border border-theme-yellow/20 bg-theme-yellow/5 p-4 animate-in fade-in slide-in-from-bottom-1 duration-300">
      <div className="flex items-start gap-2.5">
        <CalendarCheck className="mt-0.5 size-4 shrink-0 text-theme-yellow" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold text-neutral-100">
            Sync timetable to Google Calendar?
          </p>
          <p className="mt-1 text-xs leading-relaxed text-neutral-400">
            This will create or update {eventCount ?? "your"} recurring weekly class events,
            with popup reminders through the end of the semester.
          </p>
          {onConfirm ? (
            <button
              type="button"
              onClick={onConfirm}
              className="mt-3 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2 text-sm font-bold text-black transition-opacity hover:opacity-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/40"
            >
              <CalendarCheck className="size-4" />
              Confirm &amp; sync
            </button>
          ) : (
            <p className="mt-2 text-xs text-neutral-500">Confirmation is no longer pending.</p>
          )}
        </div>
      </div>
    </div>
  )
}
