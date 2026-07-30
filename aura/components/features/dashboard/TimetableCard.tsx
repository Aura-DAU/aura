"use client"

import { CalendarDays, Loader2 } from "lucide-react"
import { useTimetable } from "@/hooks/use-timetable"

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] as const

function todayDayOfWeek(): number {
  // JS Date#getDay(): 0=Sun … 6=Sat. The backend's day_of_week (see
  // pipeline/timetable/service.py DAY_NAMES) is 0=Mon … 6=Sun. Convert
  // so slot.day_of_week comparisons below actually match today.
  const jsDay = new Date().getDay()
  return (jsDay + 6) % 7
}

/** Displays today's classes from the live AURA timetable API. */
export function TimetableCard() {
  const { data, loading, error, refetch } = useTimetable()
  const today = todayDayOfWeek()
  const entries = (data?.timetable ?? [])
    .filter((slot) => slot.day_of_week === today)
    .slice()
    .sort((a, b) => a.start_time.localeCompare(b.start_time))

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center gap-2">
        <CalendarDays className="size-4 shrink-0 text-theme-yellow" />
        <h2 className="text-sm font-semibold text-neutral-200">
          Today&apos;s Timetable
          <span className="ml-1.5 text-xs font-normal text-neutral-500">
            — {DAY_NAMES[today - 1]}
          </span>
        </h2>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-xs text-neutral-500">
          <Loader2 className="size-3.5 animate-spin" /> Loading today&apos;s classes…
        </div>
      ) : error ? (
        <p className="text-xs text-neutral-500">
          Unable to load timetable right now.{" "}
          <button type="button" onClick={() => refetch()} className="underline underline-offset-2">
            Try again
          </button>
        </p>
      ) : entries.length === 0 ? (
        <p className="text-xs text-neutral-500">No classes today.</p>
      ) : (
        <ul className="space-y-2">
          {entries.map((slot) => (
            <li
              key={slot.id}
              className="flex items-start justify-between gap-3 rounded-xl border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2.5"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium text-neutral-100">
                  {slot.course_name}
                  {slot.course_code ? ` (${slot.course_code})` : ""}
                </p>
                {slot.room ? (
                  <p className="mt-0.5 text-xs text-neutral-500">{slot.room}</p>
                ) : null}
              </div>
              <span className="shrink-0 rounded-full bg-theme-gray-lighter px-2 py-0.5 text-xs text-neutral-400">
                {slot.start_time} – {slot.end_time}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
