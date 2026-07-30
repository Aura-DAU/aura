"use client"

import { useState } from "react"
import { CalendarDays, Loader2 } from "lucide-react"
import { useTimetable, TimetableSlot } from "@/hooks/use-timetable"
import { useCohortProfile } from "@/hooks/use-cohort-profile"
import { TimetableSetupCard } from "@/components/features/dashboard/TimetableSetupCard"

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"] as const
const DAY_SHORT_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] as const

function todayDayOfWeek(): number {
  // JS: 0=Sun … 6=Sat → convert to 1=Mon … 7=Sun used by timetable slots
  const jsDay = new Date().getDay()
  return jsDay === 0 ? 7 : jsDay
}

function ClassCard({ slot }: { slot: TimetableSlot }) {
  return (
    <div className="flex flex-col rounded-xl border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2.5 hover:bg-theme-gray-light/60 transition-colors">
      <p className="text-xs font-semibold text-neutral-100 leading-snug">
        {slot.course_name}
        {slot.course_code ? ` (${slot.course_code})` : ""}
      </p>
      <div className="mt-2 flex items-end justify-between gap-2">
        <div className="min-w-0 flex-1 text-[10px] text-neutral-400">
          {slot.room ? <p className="truncate text-theme-yellow/80">{slot.room}</p> : null}
          {slot.faculty_name ? <p className="truncate">{slot.faculty_name}</p> : null}
        </div>
        <span className="shrink-0 rounded-md bg-theme-gray-lighter/80 px-1.5 py-0.5 text-[10px] font-medium text-neutral-300">
          {slot.start_time} – {slot.end_time}
        </span>
      </div>
    </div>
  )
}

/** Displays the live AURA timetable API in a weekly grid (desktop) or day-pills (mobile).
 *  Shows a setup wizard on first visit when no cohort is configured. */
export function TimetableCard() {
  const { data, loading, error, refetch } = useTimetable()
  const { profile, loading: profileLoading } = useCohortProfile()
  
  const todayIndex = todayDayOfWeek() - 1 // 0=Mon, 6=Sun
  const [selectedDay, setSelectedDay] = useState(todayIndex)

  // Show setup card when profile is not yet configured or timetable returned a cohort-not-found error.
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

  const allSlots = data?.timetable ?? []

  // Helper to get sorted slots for a specific day
  const getSlotsForDay = (dayIndex: number) => {
    return allSlots
      .filter((slot) => slot.day_of_week === dayIndex)
      .slice()
      .sort((a, b) => a.start_time.localeCompare(b.start_time))
  }

  const mobileEntries = getSlotsForDay(selectedDay)

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center gap-2">
        <CalendarDays className="size-4 shrink-0 text-theme-yellow" />
        <h2 className="text-sm font-semibold text-neutral-200">
          My Timetable
        </h2>
      </div>

      {loading ? (
        <div className="flex items-center gap-2 text-xs text-neutral-500">
          <Loader2 className="size-3.5 animate-spin" /> Loading classes…
        </div>
      ) : error ? (
        <p className="text-xs text-neutral-500">
          Unable to load timetable right now.{" "}
          <button type="button" onClick={() => refetch()} className="underline underline-offset-2">
            Try again
          </button>
        </p>
      ) : (
        <>
          {/* MOBILE VIEW: Day Selector + List */}
          <div className="block md:hidden">
            <div className="mb-4 flex snap-x gap-2 overflow-x-auto pb-2 scrollbar-hide">
              {DAY_SHORT_NAMES.map((day, idx) => (
                <button
                  key={day}
                  type="button"
                  onClick={() => setSelectedDay(idx)}
                  className={`shrink-0 snap-start rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${
                    selectedDay === idx
                      ? "bg-theme-yellow text-theme-black"
                      : "bg-theme-gray-light text-neutral-400 hover:bg-theme-gray-lighter hover:text-neutral-200"
                  }`}
                >
                  {day}
                </button>
              ))}
            </div>
            {mobileEntries.length === 0 ? (
              <p className="text-xs text-neutral-500 py-4 text-center">No classes scheduled.</p>
            ) : (
              <div className="flex flex-col gap-2">
                {mobileEntries.map((slot) => (
                  <ClassCard key={slot.id} slot={slot} />
                ))}
              </div>
            )}
          </div>

          {/* DESKTOP VIEW: Weekly Grid */}
          <div className="hidden md:grid grid-cols-6 xl:grid-cols-7 gap-3">
            {/* Show Mon-Sat always, include Sun only on extra large screens or if needed */}
            {DAY_NAMES.slice(0, 6).map((day, idx) => {
              const daySlots = getSlotsForDay(idx)
              const isToday = todayIndex === idx
              return (
                <div key={day} className="flex flex-col gap-2">
                  <div className={`text-center py-1 text-xs font-semibold rounded-md ${isToday ? 'bg-theme-yellow/20 text-theme-yellow' : 'text-neutral-400'}`}>
                    {day}
                  </div>
                  {daySlots.length === 0 ? (
                    <div className="flex-1 rounded-xl border border-dashed border-theme-gray-light/30 flex items-center justify-center py-6">
                      <span className="text-[10px] text-neutral-600">Free</span>
                    </div>
                  ) : (
                    daySlots.map((slot) => <ClassCard key={slot.id} slot={slot} />)
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
