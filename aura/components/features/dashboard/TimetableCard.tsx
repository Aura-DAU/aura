"use client"

import { CalendarDays, Loader2 } from "lucide-react"
import { useTimetable } from "@/hooks/use-timetable"
import { useCohortProfile } from "@/hooks/use-cohort-profile"
import { TimetableSetupCard } from "@/components/features/dashboard/TimetableSetupCard"

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] as const

function todayDayOfWeek(): number {
  // JS: 0=Sun … 6=Sat → convert to 1=Mon … 7=Sun used by timetable slots
  const jsDay = new Date().getDay()
  return jsDay === 0 ? 7 : jsDay
}

/** Displays today's classes from the live AURA timetable API.
 *  Shows a setup wizard on first visit when no cohort is configured. */
export function TimetableCard() {
  const { data, loading, error, refetch } = useTimetable()
  const { profile, loading: profileLoading } = useCohortProfile()
  const today = todayDayOfWeek()

  const entries = (data?.timetable ?? [])
    .filter((slot) => slot.day_of_week === today - 1)
    .slice()
    .sort((a, b) => a.start_time.localeCompare(b.start_time))

  // Show setup card when profile is not yet configured or timetable returned a
  // cohort-not-found error (the backend returns a 409 with a descriptive message).
  const notConfigured =
    (!profileLoading && profile && !profile.is_configured) ||
    (error !== null && (
      error.toLowerCase().includes("not set up") ||
      error.toLowerCase().includes("cohort") ||
      error.toLowerCase().includes("section")
    ))

  if (profileLoading && !data) {
    return (
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
        <div className="flex items-center gap-2 text-xs text-neutral-500">
          <Loader2 className="size-3.5 animate-spin" /> Loading your timetable…
        </div>
      </div>
    )
  }

  if (notConfigured) {
    return <TimetableSetupCard onComplete={() => void refetch()} />
  }

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
        <p className="text-xs text-neutral-500">No classes today. Enjoy your break!</p>
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
                {slot.faculty_name ? (
                  <p className="mt-0.5 text-xs text-neutral-500">{slot.faculty_name}</p>
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
