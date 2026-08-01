"use client"

import { useState } from "react"
import { Loader2, Trash2, X } from "lucide-react"
import { TimetableSlot } from "@/hooks/use-timetable"
import { useTimetableEditor } from "@/hooks/use-timetable-editor"

const DAY_OPTIONS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"] as const
const SESSION_TYPES = [
  { value: "lecture", label: "Lecture" },
  { value: "lab", label: "Lab" },
  { value: "tutorial", label: "Tutorial" },
] as const

interface TimetableEditModalProps {
  /** "add" for a brand-new entry, "edit" for an existing slot (custom override or plain master row). */
  mode: "add" | "edit"
  slot?: TimetableSlot
  /** Prefill for "add" mode, e.g. from the grid cell/row the person clicked. */
  defaultDay?: string
  defaultStart?: string
  defaultEnd?: string
  onClose: () => void
  /** Called after a successful save/remove so the parent can refetch the timetable. */
  onSaved: () => void
}

const inputClass =
  "w-full rounded-lg border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2 text-xs text-neutral-100 outline-none focus:border-theme-yellow/60"
const labelClass = "mb-1 block text-[10px] font-medium uppercase tracking-wide text-neutral-500"

export function TimetableEditModal({
  mode,
  slot,
  defaultDay,
  defaultStart,
  defaultEnd,
  onClose,
  onSaved,
}: TimetableEditModalProps) {
  const { saving, error, applyChange, removeChange, clearError } = useTimetableEditor()

  const [day, setDay] = useState(slot?.day ?? defaultDay ?? "Monday")
  const [startTime, setStartTime] = useState(slot?.start_time ?? defaultStart ?? "")
  const [endTime, setEndTime] = useState(slot?.end_time ?? defaultEnd ?? "")
  const [courseCode, setCourseCode] = useState(slot?.course_code ?? "")
  const [courseName, setCourseName] = useState(slot?.course_name ?? "")
  const [sessionType, setSessionType] = useState<"lecture" | "lab" | "tutorial">(
    slot?.session_type ?? "lecture"
  )
  const [room, setRoom] = useState(slot?.room ?? "")
  const [facultyName, setFacultyName] = useState(slot?.faculty_name ?? "")
  const [note, setNote] = useState("")

  // Once a class already has a personal override on it (is_custom), the
  // backend has no way to further "replace" it from here — replace always
  // looks the class up by its ORIGINAL master day/time/course, which the
  // override has already changed. The safe, honest action at that point is
  // to remove the override and start over, not to silently fail a save.
  const isLockedOverride = mode === "edit" && Boolean(slot?.is_custom)

  const canSave =
    !isLockedOverride &&
    (mode === "add"
      ? Boolean(day && startTime && endTime && courseName)
      : Boolean(day && startTime && courseName))

  const handleSave = async () => {
    if (!canSave) return
    try {
      await applyChange({
        kind: mode === "add" ? "add" : "replace",
        day,
        start_time: startTime,
        end_time: endTime || undefined,
        course_code: courseCode || undefined,
        course_name: courseName,
        session_type: sessionType,
        room: room || undefined,
        faculty_name: facultyName || undefined,
        note: note || undefined,
      })
      onSaved()
    } catch {
      // error is already surfaced via the hook's `error` state
    }
  }

  const handleRemove = async () => {
    if (!slot) return
    try {
      if (slot.is_custom) {
        // This slot only exists because of a previous override (an "add"
        // or "replace") — undo that override directly by its own id.
        await removeChange(slot.id)
      } else {
        // Plain master-schedule row: record a "remove" override so it
        // stops showing on this student's own timetable.
        await applyChange({
          kind: "remove",
          day: slot.day,
          start_time: slot.start_time,
          course_code: slot.course_code || undefined,
        })
      }
      onSaved()
    } catch {
      // error is already surfaced via the hook's `error` state
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 sm:items-center sm:p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[90vh] w-full overflow-y-auto rounded-t-2xl border border-theme-gray-light bg-theme-gray p-5 sm:max-w-md sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-neutral-100">
            {mode === "add" ? "Add a class" : "Edit class"}
          </h3>
          <button type="button" onClick={onClose} className="text-neutral-500 hover:text-neutral-300">
            <X className="size-4" />
          </button>
        </div>

        {error && (
          <p className="mb-3 rounded-lg border border-theme-red/30 bg-theme-red/10 px-3 py-2 text-xs text-red-400">
            {error}
          </p>
        )}

        {isLockedOverride ? (
          <div className="space-y-4">
            <p className="text-xs leading-relaxed text-neutral-400">
              This class already has a personal change on it, so it can&apos;t be edited further from here —
              remove the change first, then add it again the way you&apos;d like.
            </p>
            <div className="rounded-xl border border-theme-gray-light bg-theme-gray-light/40 px-3 py-2.5 text-xs">
              <p className="font-semibold text-neutral-100">
                {courseName}
                {courseCode ? ` (${courseCode})` : ""}
              </p>
              <p className="mt-1 text-neutral-400">
                {day} • {startTime}–{endTime}
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleRemove()}
              disabled={saving}
              className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-theme-red/40 py-2.5 text-xs font-semibold text-red-400 transition-colors hover:bg-theme-red/10 disabled:opacity-40"
            >
              {saving ? <Loader2 className="size-3.5 animate-spin" /> : <Trash2 className="size-3.5" />}
              Remove this change
            </button>
          </div>
        ) : (
          <div className="space-y-3">
            <div>
              <label className={labelClass}>Day</label>
              {mode === "edit" ? (
                <div className={inputClass}>
                  <span className="text-neutral-400">{day} (fixed — this identifies the class)</span>
                </div>
              ) : (
                <select
                  value={day}
                  onChange={(e) => setDay(e.target.value)}
                  className={inputClass}
                >
                  {DAY_OPTIONS.map((d) => (
                    <option key={d} value={d}>
                      {d}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelClass}>Start time</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>End time</label>
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className={labelClass}>Course name</label>
              <input
                type="text"
                value={courseName}
                onChange={(e) => setCourseName(e.target.value)}
                placeholder="e.g. Data Communication"
                className={inputClass}
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelClass}>Course code</label>
                <input
                  type="text"
                  value={courseCode}
                  onChange={(e) => setCourseCode(e.target.value)}
                  placeholder="e.g. CT303"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Type</label>
                <select
                  value={sessionType}
                  onChange={(e) => setSessionType(e.target.value as typeof sessionType)}
                  className={inputClass}
                >
                  {SESSION_TYPES.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className={labelClass}>Room</label>
                <input
                  type="text"
                  value={room}
                  onChange={(e) => setRoom(e.target.value)}
                  placeholder="e.g. LT-2"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Faculty</label>
                <input
                  type="text"
                  value={facultyName}
                  onChange={(e) => setFacultyName(e.target.value)}
                  placeholder="e.g. SS"
                  className={inputClass}
                />
              </div>
            </div>

            <div>
              <label className={labelClass}>Note (optional)</label>
              <input
                type="text"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Why you're changing this — just for your own record"
                className={inputClass}
              />
            </div>

            <div className="flex gap-2 pt-1">
              {mode === "edit" && (
                <button
                  type="button"
                  onClick={() => {
                    clearError()
                    void handleRemove()
                  }}
                  disabled={saving}
                  className="flex items-center justify-center gap-1.5 rounded-xl border border-theme-red/40 px-3 py-2.5 text-xs font-semibold text-red-400 transition-colors hover:bg-theme-red/10 disabled:opacity-40"
                >
                  <Trash2 className="size-3.5" /> Remove
                </button>
              )}
              <button
                type="button"
                onClick={() => void handleSave()}
                disabled={!canSave || saving}
                className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-2.5 text-xs font-bold text-black transition-opacity hover:opacity-90 disabled:opacity-40"
              >
                {saving && <Loader2 className="size-3.5 animate-spin" />}
                {mode === "add" ? "Add class" : "Save changes"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
