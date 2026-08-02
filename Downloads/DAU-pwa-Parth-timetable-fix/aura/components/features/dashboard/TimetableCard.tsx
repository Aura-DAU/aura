"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { CalendarDays, Loader2, Sparkles, Settings2 } from "lucide-react"
import { useTimetable, TimetableSlot } from "@/hooks/use-timetable"
import { TimetableSetupCard } from "@/components/features/dashboard/TimetableSetupCard"

// Classes only run Monday–Friday, so that's all we show.
const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] as const
const DAY_SHORT_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri"] as const

const SETUP_PROMPT =
  "I'd like to set up my personal timetable — please ask me for my section and electives."

function todayDayOfWeek(): number {
  // JS: 0=Sun … 6=Sat → convert to 0=Mon … 4=Fri used by DAY_NAMES/DAY_SHORT_NAMES.
  // On a Saturday or Sunday there's no matching column, so default to Monday.
  const jsDay = new Date().getDay()
  if (jsDay === 0 || jsDay === 6) return 0
  return jsDay - 1
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

function isElective(slot: TimetableSlot): boolean {
  return (slot.course_type ?? "").toLowerCase().includes("elective")
}

// Deterministic pastel color per course_code, so the same subject always
// lands on the same color every time the grid re-renders (mirrors the
// source timetable spreadsheet, where each subject has its own fill color).
const SUBJECT_PALETTE = [
  { bg: "bg-orange-400/25", text: "text-orange-200", border: "border-orange-400/40" },
  { bg: "bg-sky-400/25", text: "text-sky-200", border: "border-sky-400/40" },
  { bg: "bg-emerald-400/25", text: "text-emerald-200", border: "border-emerald-400/40" },
  { bg: "bg-neutral-400/25", text: "text-neutral-200", border: "border-neutral-400/40" },
  { bg: "bg-fuchsia-400/25", text: "text-fuchsia-200", border: "border-fuchsia-400/40" },
  { bg: "bg-amber-400/25", text: "text-amber-200", border: "border-amber-400/40" },
  { bg: "bg-indigo-400/25", text: "text-indigo-200", border: "border-indigo-400/40" },
  { bg: "bg-rose-400/25", text: "text-rose-200", border: "border-rose-400/40" },
] as const

function colorForSubject(key: string) {
  let hash = 0
  for (let i = 0; i < key.length; i++) hash = (hash * 31 + key.charCodeAt(i)) >>> 0
  return SUBJECT_PALETTE[hash % SUBJECT_PALETTE.length]
}

/** One cell in the weekly grid: subject code, room, and a color tied to the subject. */
function GridCell({ slot }: { slot: TimetableSlot }) {
  const color = colorForSubject(slot.course_code || slot.course_name)
  return (
    <div
      title={`${slot.course_name}${slot.faculty_name ? ` • ${slot.faculty_name}` : ""}`}
      className={`flex h-full flex-col items-center justify-center gap-0.5 rounded-lg border px-1 py-2 text-center leading-tight ${color.bg} ${color.border}`}
    >
      <p className={`text-[10px] font-semibold ${color.text}`}>
        {slot.course_code || slot.course_name}
      </p>
      {slot.room ? <p className="text-[9px] text-neutral-300/70">{slot.room}</p> : null}
    </div>
  )
}

/** A blank cell for a day/time with nothing scheduled. */
function EmptyCell() {
  return (
    <div className="flex h-full items-center justify-center rounded-lg border border-dashed border-theme-gray-light/30 py-2">
      <span className="text-[10px] text-neutral-600">–</span>
    </div>
  )
}

interface GridRow {
  start: string
  end: string
  cells: Partial<Record<number, TimetableSlot>>
}

/** Buckets slots into one row per distinct start time, with a column per
 * weekday — the same "time down the side, day across the top" shape as
 * the source timetable spreadsheet, instead of one independent list per day. */
function buildGridRows(slots: TimetableSlot[]): GridRow[] {
  const byStart = new Map<string, GridRow>()
  for (const slot of slots) {
    let row = byStart.get(slot.start_time)
    if (!row) {
      row = { start: slot.start_time, end: slot.end_time, cells: {} }
      byStart.set(slot.start_time, row)
    }
    row.cells[slot.day_of_week] = slot
    if (slot.end_time > row.end) row.end = slot.end_time
  }
  return Array.from(byStart.values()).sort((a, b) => a.start.localeCompare(b.start))
}

/** Displays the live AURA timetable API in a weekly grid (desktop) or day-pills (mobile).
 *
 *  On first login, before the student has told AURA their section/electives, the backend
 *  already returns a sensible default (year/branch inferred from their email, section "A")
 *  — see service.get_effective_timetable's `is_common` fallback. This card shows that
 *  default immediately rather than gating the whole view behind a setup wizard; a small
 *  banner nudges the student to personalize it in chat instead. */
export function TimetableCard() {
  const { data, loading, error, refetch } = useTimetable()
  const router = useRouter()

  const todayIndex = todayDayOfWeek() // 0=Mon … 4=Fri (weekends default to Monday)
  const [selectedDay, setSelectedDay] = useState(todayIndex)
  const [showManualSetup, setShowManualSetup] = useState(false)

  const handlePersonalizeInChat = () => {
    router.push(`/?prompt=${encodeURIComponent(SETUP_PROMPT)}`)
  }

  if (loading && !data) {
    return (
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
        <div className="flex items-center gap-2 text-xs text-neutral-500">
          <Loader2 className="size-3.5 animate-spin" /> Loading your timetable…
        </div>
      </div>
    )
  }

  if (showManualSetup) {
    return (
      <TimetableSetupCard
        onComplete={() => {
          setShowManualSetup(false)
          void refetch()
        }}
      />
    )
  }

  const allSlots = data?.timetable ?? []
  const needsConfiguration = Boolean(data?.needs_configuration || data?.is_common)

  // Helper to get sorted slots for a specific day
  const getSlotsForDay = (dayIndex: number) => {
    return allSlots
      .filter((slot) => slot.day_of_week === dayIndex)
      .slice()
      .sort((a, b) => a.start_time.localeCompare(b.start_time))
  }

  const mobileEntries = getSlotsForDay(selectedDay)

  const coreSlots = allSlots.filter((slot) => !isElective(slot))
  const electiveSlots = allSlots.filter(isElective)
  const coreRows = buildGridRows(coreSlots)
  const electiveRows = buildGridRows(electiveSlots)

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <CalendarDays className="size-4 shrink-0 text-theme-yellow" />
          <h2 className="text-sm font-semibold text-neutral-200">
            My Timetable
          </h2>
        </div>
        <button
          type="button"
          onClick={() => setShowManualSetup(true)}
          className="flex shrink-0 items-center gap-1 text-[10px] font-medium text-neutral-500 hover:text-neutral-300"
        >
          <Settings2 className="size-3" /> Customize
        </button>
      </div>

      {needsConfiguration && !loading && !error && (
        <button
          type="button"
          onClick={handlePersonalizeInChat}
          className="mb-4 flex w-full items-start gap-2 rounded-xl border border-theme-yellow/30 bg-theme-yellow/5 px-3 py-2.5 text-left transition-colors hover:bg-theme-yellow/10"
        >
          <Sparkles className="mt-0.5 size-3.5 shrink-0 text-theme-yellow" />
          <span className="text-[11px] leading-relaxed text-neutral-300">
            {data?.is_common
              ? "This is the default timetable for your year (Section A). "
              : "Your core schedule is set — "}
            Tell AURA your section and electives in chat to personalize it.
          </span>
        </button>
      )}

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
                  className={`shrink-0 snap-start rounded-full px-4 py-1.5 text-xs font-semibold transition-colors ${selectedDay === idx
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

          {/* DESKTOP VIEW: Weekly Grid — time down the side, day across the top,
              same shape as the source timetable spreadsheet, with electives
              broken out into their own band underneath. */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full table-fixed border-separate border-spacing-1.5">
              <colgroup>
                <col className="w-14" />
                {DAY_NAMES.map((day) => (
                  <col key={day} />
                ))}
              </colgroup>
              <thead>
                <tr>
                  <th aria-hidden className="p-0" />
                  {DAY_NAMES.map((day, idx) => (
                    <th
                      key={day}
                      className={`rounded-md py-1 text-xs font-semibold ${todayIndex === idx ? "bg-theme-yellow/20 text-theme-yellow" : "text-neutral-400"
                        }`}
                    >
                      {day}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {coreRows.length === 0 ? (
                  <tr>
                    <td colSpan={DAY_NAMES.length + 1} className="py-6 text-center text-[10px] text-neutral-600">
                      No classes scheduled.
                    </td>
                  </tr>
                ) : (
                  coreRows.map((row) => (
                    <tr key={row.start} className="h-16">
                      <td className="align-middle text-[10px] font-medium leading-tight text-neutral-500">
                        {row.start}
                        <br />
                        {row.end}
                      </td>
                      {DAY_NAMES.map((_, idx) => (
                        <td key={idx} className="h-16 align-middle">
                          {row.cells[idx] ? <GridCell slot={row.cells[idx]!} /> : <EmptyCell />}
                        </td>
                      ))}
                    </tr>
                  ))
                )}

                {electiveRows.length > 0 && (
                  <>
                    <tr>
                      <td colSpan={DAY_NAMES.length + 1} className="pt-2">
                        <div className="rounded-md bg-theme-yellow/15 py-1 text-center text-[10px] font-semibold uppercase tracking-wide text-theme-yellow">
                          Elective
                        </div>
                      </td>
                    </tr>
                    {electiveRows.map((row) => (
                      <tr key={row.start} className="h-16">
                        <td className="align-middle text-[10px] font-medium leading-tight text-neutral-500">
                          {row.start}
                          <br />
                          {row.end}
                        </td>
                        {DAY_NAMES.map((_, idx) => (
                          <td key={idx} className="h-16 align-middle">
                            {row.cells[idx] ? <GridCell slot={row.cells[idx]!} /> : <EmptyCell />}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}