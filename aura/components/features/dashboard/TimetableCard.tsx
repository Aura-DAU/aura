"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { CalendarDays, Loader2, Sparkles, Settings2, Pencil, Plus, CalendarCheck2 } from "lucide-react"
import { useTimetable, TimetableSlot } from "@/hooks/use-timetable"
import { useGoogleCalendarSync } from "@/hooks/use-google-calendar-sync"
import { TimetableSetupCard } from "@/components/features/dashboard/TimetableSetupCard"
import { TimetableEditModal } from "@/components/features/dashboard/TimetableEditModal"

// Classes only run Monday–Friday, so that's all we show.
const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] as const
const DAY_SHORT_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri"] as const

const SETUP_PROMPT =
  "I'd like to set up my personal timetable — please ask me for my section and electives."

function todayDayOfWeek(): number {
  // Get current time in IST so the schedule rolls over at university midnight,
  // not the student's local OS midnight if they are traveling.
  const istString = new Date().toLocaleString("en-US", { timeZone: "Asia/Kolkata" })
  const jsDay = new Date(istString).getDay() // 0=Sun … 6=Sat
  // Convert to 0=Mon … 4=Fri used by DAY_NAMES/DAY_SHORT_NAMES.
  // On a Saturday or Sunday there's no matching column, so default to Monday.
  if (jsDay === 0 || jsDay === 6) return 0
  return jsDay - 1
}

function ClassCard({ slot, onClick }: { slot: TimetableSlot; onClick?: () => void }) {
  const content = (
    <>
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
    </>
  )

  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="flex w-full flex-col rounded-xl border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2.5 text-left transition-colors hover:bg-theme-gray-light/60 hover:ring-1 hover:ring-theme-yellow/40"
      >
        {content}
      </button>
    )
  }

  return (
    <div className="flex flex-col rounded-xl border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2.5 hover:bg-theme-gray-light/60 transition-colors">
      {content}
    </div>
  )
}

function isElective(slot: TimetableSlot): boolean {
  return (slot.course_type ?? "").toLowerCase().includes("elective")
}

// Deterministic pastel color per course_code, so the same subject always
// lands on the same color every time the grid re-renders (mirrors the
// source timetable spreadsheet, where each subject has its own fill color).
// Single fixed color for every grid cell — matches the neutral dark card
// style used elsewhere in the timetable (mobile ClassCard, etc.), so every
// class looks the same regardless of subject.
const SLOT_COLOR = { bg: "bg-theme-gray-light/40", text: "text-neutral-100", border: "border-theme-gray-light" } as const

function colorForSubject() {
  return SLOT_COLOR
}

/** One cell in the weekly grid: subject code, room, and a color tied to the subject. */
function GridCell({ slot, onClick }: { slot: TimetableSlot; onClick?: () => void }) {
  const color = colorForSubject()
  const classes = `flex h-full w-full flex-col items-center justify-center gap-0.5 rounded-lg border px-1 py-2 text-center leading-tight transition-transform ${color.bg} ${color.border} ${onClick ? "hover:scale-[1.03] hover:ring-1 hover:ring-theme-yellow/50" : ""
    }`
  const inner = (
    <>
      <p className={`text-[10px] font-semibold ${color.text}`}>
        {slot.course_code || slot.course_name}
      </p>
      {slot.room ? <p className="text-[9px] text-neutral-300/70">{slot.room}</p> : null}
    </>
  )
  if (onClick) {
    return (
      <button type="button" onClick={onClick} title={`${slot.course_name}${slot.faculty_name ? ` • ${slot.faculty_name}` : ""} — tap to edit`} className={classes}>
        {inner}
      </button>
    )
  }
  return (
    <div title={`${slot.course_name}${slot.faculty_name ? ` • ${slot.faculty_name}` : ""}`} className={classes}>
      {inner}
    </div>
  )
}

/** A blank cell for a day/time with nothing scheduled. In edit mode this
 * becomes a "+" button that opens the add-class modal prefilled for that
 * exact day and time row. */
function EmptyCell({ onClick }: { onClick?: () => void }) {
  if (onClick) {
    return (
      <button
        type="button"
        onClick={onClick}
        title="Add a class here"
        className="flex h-full w-full items-center justify-center rounded-lg border border-dashed border-theme-gray-light/40 py-2 text-neutral-600 transition-colors hover:border-theme-yellow/50 hover:text-theme-yellow"
      >
        <Plus className="size-3" />
      </button>
    )
  }
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
  const { status: calendarStatus } = useGoogleCalendarSync()

  const todayIndex = todayDayOfWeek() // 0=Mon … 4=Fri (weekends default to Monday)
  const [selectedDay, setSelectedDay] = useState(todayIndex)
  const [showManualSetup, setShowManualSetup] = useState(false)
  const [editMode, setEditMode] = useState(false)

  // Describes whichever add/edit modal is currently open, or null when closed.
  const [activeEdit, setActiveEdit] = useState<
    | { mode: "edit"; slot: TimetableSlot }
    | { mode: "add"; day: string; start?: string; end?: string }
    | null
  >(null)

  const handlePersonalizeInChat = () => {
    router.push(`/?prompt=${encodeURIComponent(SETUP_PROMPT)}`)
  }

  const handleSaved = () => {
    setActiveEdit(null)
    void refetch()
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

  const coreSlots = allSlots.filter((slot) => !isElective(slot) && slot.session_type !== "lab" && slot.session_type !== "tutorial")
  const electiveSlots = allSlots.filter((slot) => isElective(slot) && slot.session_type !== "lab" && slot.session_type !== "tutorial")
  const labSlots = allSlots.filter((slot) => slot.session_type === "lab" || slot.session_type === "tutorial")
  const coreRows = buildGridRows(coreSlots)
  const electiveRows = buildGridRows(electiveSlots)
  const labRows = buildGridRows(labSlots)

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray p-5">
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <CalendarDays className="size-4 shrink-0 text-theme-yellow" />
          <h2 className="text-sm font-semibold text-neutral-200">
            My Timetable
          </h2>
          {calendarStatus === "connected" && (
            <span
              title="Changes here keep your Google Calendar in sync"
              className="hidden items-center gap-1 rounded-full bg-emerald-400/10 px-2 py-0.5 text-[9px] font-medium text-emerald-300 sm:flex"
            >
              <CalendarCheck2 className="size-2.5" /> Synced
            </span>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-3">
          {editMode && (
            <button
              type="button"
              onClick={() => setActiveEdit({ mode: "add", day: DAY_NAMES[todayIndex] })}
              className="flex items-center gap-1 text-[10px] font-medium text-theme-yellow hover:text-theme-yellow/80"
            >
              <Plus className="size-3" /> Add class
            </button>
          )}
          <button
            type="button"
            onClick={() => setEditMode((v) => !v)}
            className={`flex items-center gap-1 text-[10px] font-medium transition-colors ${editMode ? "text-theme-yellow" : "text-neutral-500 hover:text-neutral-300"
              }`}
          >
            <Pencil className="size-3" /> {editMode ? "Done" : "Edit"}
          </button>
          <button
            type="button"
            onClick={() => setShowManualSetup(true)}
            className="flex items-center gap-1 text-[10px] font-medium text-neutral-500 hover:text-neutral-300"
          >
            <Settings2 className="size-3" /> Customize
          </button>
        </div>
      </div>

      {editMode && (
        <p className="mb-3 text-[10px] leading-relaxed text-neutral-500">
          Tap any class to edit or remove it, or tap a blank slot to add one.
          {calendarStatus !== "connected" && (
            <>
              {" "}
              <Link href="/settings/calendar" className="underline underline-offset-2 hover:text-neutral-300">
                Connect Google Calendar
              </Link>{" "}
              to keep changes synced automatically.
            </>
          )}
        </p>
      )}

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
                  <ClassCard
                    key={slot.id}
                    slot={slot}
                    onClick={editMode ? () => setActiveEdit({ mode: "edit", slot }) : undefined}
                  />
                ))}
              </div>
            )}
            {editMode && (
              <button
                type="button"
                onClick={() => setActiveEdit({ mode: "add", day: DAY_NAMES[selectedDay] })}
                className="mt-2 flex w-full items-center justify-center gap-1.5 rounded-xl border border-dashed border-theme-gray-light/50 py-2 text-xs font-medium text-neutral-400 hover:border-theme-yellow/50 hover:text-theme-yellow"
              >
                <Plus className="size-3.5" /> Add a class on {DAY_NAMES[selectedDay]}
              </button>
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
                      {DAY_NAMES.map((dayName, idx) => (
                        <td key={idx} className="h-16 align-middle">
                          {row.cells[idx] ? (
                            <GridCell
                              slot={row.cells[idx]!}
                              onClick={editMode ? () => setActiveEdit({ mode: "edit", slot: row.cells[idx]! }) : undefined}
                            />
                          ) : (
                            <EmptyCell
                              onClick={
                                editMode
                                  ? () => setActiveEdit({ mode: "add", day: dayName, start: row.start, end: row.end })
                                  : undefined
                              }
                            />
                          )}
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
                        {DAY_NAMES.map((dayName, idx) => (
                          <td key={idx} className="h-16 align-middle">
                            {row.cells[idx] ? (
                              <GridCell
                                slot={row.cells[idx]!}
                                onClick={editMode ? () => setActiveEdit({ mode: "edit", slot: row.cells[idx]! }) : undefined}
                              />
                            ) : (
                              <EmptyCell
                                onClick={
                                  editMode
                                    ? () => setActiveEdit({ mode: "add", day: dayName, start: row.start, end: row.end })
                                    : undefined
                                }
                              />
                            )}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </>
                )}

                {labRows.length > 0 && (
                  <>
                    <tr>
                      <td colSpan={DAY_NAMES.length + 1} className="pt-2">
                        <div className="rounded-md bg-theme-yellow/15 py-1 text-center text-[10px] font-semibold uppercase tracking-wide text-theme-yellow">
                          Lab / Tutorial
                        </div>
                      </td>
                    </tr>
                    {labRows.map((row) => (
                      <tr key={row.start} className="h-16">
                        <td className="align-middle text-[10px] font-medium leading-tight text-neutral-500">
                          {row.start}
                          <br />
                          {row.end}
                        </td>
                        {DAY_NAMES.map((dayName, idx) => (
                          <td key={idx} className="h-16 align-middle">
                            {row.cells[idx] ? (
                              <GridCell
                                slot={row.cells[idx]!}
                                onClick={editMode ? () => setActiveEdit({ mode: "edit", slot: row.cells[idx]! }) : undefined}
                              />
                            ) : (
                              <EmptyCell
                                onClick={
                                  editMode
                                    ? () => setActiveEdit({ mode: "add", day: dayName, start: row.start, end: row.end })
                                    : undefined
                                }
                              />
                            )}
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

      {activeEdit && (
        <TimetableEditModal
          mode={activeEdit.mode}
          slot={activeEdit.mode === "edit" ? activeEdit.slot : undefined}
          defaultDay={activeEdit.mode === "add" ? activeEdit.day : undefined}
          defaultStart={activeEdit.mode === "add" ? activeEdit.start : undefined}
          defaultEnd={activeEdit.mode === "add" ? activeEdit.end : undefined}
          onClose={() => setActiveEdit(null)}
          onSaved={handleSaved}
        />
      )}
    </div>
  )
}