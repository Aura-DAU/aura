"use client"

import React, { useEffect, useState } from "react"
import { Calendar, Users, ArrowRight, Loader2, AlertCircle, Clock } from "lucide-react"
import { apiFetch, ensureSession } from "@/lib/auth-client"

interface FacultyDashboardProps {
  userName: string
  departmentName?: string
  onSelectPrompt: (text: string) => void
}

type CardState = "loading" | "done" | "error"

/**
 * A single line in the merged "Today's Schedule" card — either a class
 * from AURA's timetable_master (via /api/timetable/me) or a meeting from
 * the faculty member's own Google Calendar (via /api/calendar/meetings,
 * server/api/routes/calendar_routes.py::get_my_calendar_meetings ->
 * pipeline.google_calendar.meetings_service.get_my_meetings). Both are
 * normalized to the same shape and merged into one time-sorted list.
 */
interface ScheduleItem {
  startTime: string   // "HH:MM", 24h, for sorting/display
  label: string        // formatted line, ready to render
}

function _fmtClassLine(s: {
  start_time: string; end_time: string; course_code: string
  course_name: string; room?: string | null
}): string {
  return `${s.start_time}\u2013${s.end_time}  ${s.course_code} ${s.course_name}${s.room ? ` (${s.room})` : ""}`
}

function _fmtMeetingLine(ev: { summary: string; start?: string | null; end?: string | null }): string {
  const time = (iso?: string | null) => {
    if (!iso) return ""
    const d = new Date(iso)
    return Number.isNaN(d.getTime()) ? "" : d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  }
  const startT = time(ev.start)
  const endT = time(ev.end)
  const range = startT && endT ? `${startT}\u2013${endT}` : startT
  return `${range}  \ud83d\udcc5 ${ev.summary}`.trim()
}

function _sortKey(iso: string): string {
  // Sorts "HH:MM–HH:MM  ..." class lines and Google's ISO datetimes
  // together by clock time. Class lines already start with "HH:MM".
  const m = iso.match(/^(\d{2}:\d{2})/)
  if (m) return m[1]
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? "99:99" : d.toLocaleTimeString([], { hour12: false, hour: "2-digit", minute: "2-digit" })
}

/**
 * Fetches today's slots from the faculty member's own teaching schedule
 * (server/api/routes/timetable_routes.py::get_my_timetable ->
 * service.get_faculty_timetable, resolved from timetable_master by
 * faculty_initials — see server/api/faculty_initials.json) AND their
 * Google Calendar meetings for today (if connected — see
 * /settings/calendar), merged into one time-sorted plain-text schedule.
 */
async function fetchTodaysSchedule(signal: AbortSignal): Promise<string> {
  const todayStr = new Date().toISOString().slice(0, 10) // YYYY-MM-DD, local-ish is fine for a "today" card

  const [timetableRes, meetingsRes] = await Promise.all([
    apiFetch("/api/timetable/me", { cache: "no-store", signal }),
    apiFetch(`/api/calendar/meetings?date=${todayStr}`, { cache: "no-store", signal }),
  ])

  const items: ScheduleItem[] = []

  // Match the original contract: a failed /timetable/me call is treated as
  // an error state upstream (empty string -> scheduleState "error"), same
  // as before meetings were added. A failed /calendar/meetings call is NOT
  // fatal — an unlinked/erroring calendar just means no meetings get added,
  // classes still show.
  if (!timetableRes.ok) return ""

  const timetableData = (await timetableRes.json()) as {
    timetable?: Array<{
      day_of_week: number; start_time: string; end_time: string
      course_code: string; course_name: string; room?: string | null
    }>
  }
  const slots = timetableData.timetable ?? []
  // service.py's day_of_week is 0=Monday..6=Sunday; JS Date#getDay() is
  // 0=Sunday..6=Saturday.
  const todayIdx = (new Date().getDay() + 6) % 7
  for (const s of slots.filter((s) => s.day_of_week === todayIdx)) {
    items.push({ startTime: s.start_time, label: _fmtClassLine(s) })
  }

  if (meetingsRes.ok) {
    const data = (await meetingsRes.json()) as {
      calendar_linked?: boolean
      meetings?: Array<{ summary: string; start?: string | null; end?: string | null }>
    }
    for (const ev of data.meetings ?? []) {
      items.push({ startTime: _sortKey(ev.start ?? ""), label: _fmtMeetingLine(ev) })
    }
  }

  if (items.length === 0) return "No classes or meetings scheduled today."

  return items
    .sort((a, b) => a.startTime.localeCompare(b.startTime))
    .map((i) => i.label)
    .join("\n")
}

/**
 * Fetches a single AURA chat answer for use in dashboard cards.
 * Returns the accumulated text-delta from the SSE stream.
 *
 * TODO(unirp): When faculty data routes migrate to UniRP API, update this
 * helper to call UniRP endpoints directly. Do NOT implement UniRP logic
 * until routes are confirmed. Current path: AURA RAG + ERP connector.
 */
async function fetchDashboardAnswer(
  question: string,
  signal: AbortSignal
): Promise<string> {
  const res = await apiFetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, history: [] }),
    signal,
  })

  if (!res.ok || !res.body) return ""

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let answer = ""

  try {
    while (true) {
      if (signal.aborted) {
        await reader.cancel().catch(() => {})
        break
      }
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() ?? ""
      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith("data:")) {
          const data = trimmed.slice(5).trim()
          if (data === "[DONE]") break
          try {
            const chunk = JSON.parse(data) as { type?: string; delta?: string }
            if (chunk.type === "text-delta" && typeof chunk.delta === "string") {
              answer += chunk.delta
            }
          } catch {
            /* skip malformed chunk */
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }

  return answer
}

function CardSkeleton({ rows = 2 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-2.5">
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-10 rounded-xl bg-theme-gray-light/40"
          style={{ opacity: 1 - i * 0.25 }}
        />
      ))}
    </div>
  )
}

export function FacultyDashboard({
  userName,
  departmentName = "Information & Communication Technology",
  onSelectPrompt,
}: FacultyDashboardProps) {
  const [scheduleText, setScheduleText] = useState("")
  const [scheduleState, setScheduleState] = useState<CardState>("loading")
  const [adviseeText, setAdviseeText] = useState("")
  const [adviseeState, setAdviseeState] = useState<CardState>("loading")

  useEffect(() => {
    const controller = new AbortController()
    const { signal } = controller

    const loadSchedule = () =>
      fetchTodaysSchedule(signal)
        .then((text) => {
          if (signal.aborted) return
          setScheduleText(text)
          setScheduleState(text.trim() ? "done" : "error")
        })
        .catch(() => {
          if (!signal.aborted) setScheduleState("error")
        })

    // TODO(unirp): Replace with UniRP endpoint when faculty data routes are confirmed.
    void (async () => {
      // Wait for session cookie before hitting /api/chat (avoids mount-time 401 race).
      const ok = await ensureSession()
      if (signal.aborted) return
      if (!ok) {
        setScheduleState("error")
        setAdviseeState("error")
        return
      }

      await Promise.all([
        loadSchedule(),
        fetchDashboardAnswer("How many advisees do I currently have?", signal)
          .then((text) => {
            if (signal.aborted) return
            setAdviseeText(text)
            setAdviseeState(text.trim() ? "done" : "error")
          })
          .catch(() => {
            if (!signal.aborted) setAdviseeState("error")
          }),
      ])
    })()

    // Same-tab refresh when a chat-driven timetable action applies (see
    // use-timetable.ts, which listens for the same event on the student
    // side). Faculty meeting/timetable edits via chat aren't wired up yet,
    // but this keeps the card current the moment they are, with no further
    // frontend change needed.
    const onTimetableChanged = () => {
      setScheduleState("loading")
      void loadSchedule()
    }
    window.addEventListener("aura:timetable-changed", onTimetableChanged)

    return () => {
      controller.abort()
      window.removeEventListener("aura:timetable-changed", onTimetableChanged)
    }
  }, [])

  // Attendance card is intentionally absent:
  // eCampus attendance data is unavailable. Revisit when UniRP exposes this endpoint.

  const quickPrompts = [
    "What is my class schedule today?",
    "List my BTP mentee groups",
    "Check room availability for seminar",
    "What are my responsibilities on the exam committee?",
  ]

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 text-left animate-in fade-in slide-in-from-bottom-3 duration-200">
      {/* Welcome banner */}
      <div className="mb-6 rounded-2xl border border-theme-gray-light bg-theme-gray/40 p-6 backdrop-blur-md">
        <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-bold text-transparent md:text-2xl">
          Welcome back, Prof. {userName}!
        </h1>
        <p className="mt-1 text-xs text-neutral-400">
          Faculty · {departmentName}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Today's Teaching Schedule — from timetable_master via /api/timetable/me,
            resolved by faculty_initials (see server/api/faculty_initials.json) */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
          <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            <Calendar className="size-3.5 text-theme-yellow" />
            Today&apos;s Schedule
            {scheduleState === "loading" && (
              <Loader2 className="ml-auto size-3 animate-spin text-neutral-600" />
            )}
          </h2>

          {scheduleState === "loading" ? (
            <CardSkeleton rows={2} />
          ) : scheduleState === "error" || !scheduleText.trim() ? (
            <div className="flex flex-col gap-1.5 rounded-xl border border-theme-gray-light/30 bg-theme-gray-light/10 p-3">
              <span className="flex items-center gap-1.5 text-xs text-neutral-500">
                <AlertCircle className="size-3.5 shrink-0" />
                Schedule unavailable
              </span>
              <span className="text-[10px] leading-relaxed text-neutral-600">
                {/*
                  Shown when this faculty account isn't yet resolved to a
                  faculty_initials code (see server/api/faculty_initials.json
                  and server/scripts/build_faculty_initials.py), so
                  timetable_master can't be matched to a person yet.
                */}
                AURA hasn&apos;t linked your account to a teaching schedule yet.
                Contact the administrator if this persists.
              </span>
            </div>
          ) : (
            <div className="rounded-xl border border-theme-gray-light/20 bg-theme-gray-light/20 p-3">
              <p className="line-clamp-8 whitespace-pre-line text-xs leading-relaxed text-neutral-300">
                {scheduleText}
              </p>
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-5">
          {/* Advisee Count — wired to composite_tools.get_advisee_snapshot via AURA chat */}
          <div className="flex-1 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <Users className="size-3.5 text-theme-yellow" />
              Advisees
              {adviseeState === "loading" && (
                <Loader2 className="ml-auto size-3 animate-spin text-neutral-600" />
              )}
            </h2>

            {adviseeState === "loading" ? (
              <CardSkeleton rows={1} />
            ) : adviseeState === "error" || !adviseeText.trim() ? (
              <div className="flex items-center gap-2 rounded-xl border border-theme-gray-light/30 bg-theme-gray-light/10 px-3 py-2.5">
                <AlertCircle className="size-3.5 shrink-0 text-neutral-600" />
                <span className="text-xs text-neutral-500">
                  Advisee data unavailable
                </span>
              </div>
            ) : (
              <div className="rounded-xl border border-theme-gray-light/20 bg-theme-gray-light/20 p-3">
                <p className="line-clamp-4 text-xs leading-relaxed text-neutral-300">
                  {adviseeText}
                </p>
              </div>
            )}

            <button
              type="button"
              onClick={() => onSelectPrompt("List all my advisees and their current semester details")}
              className="mt-2.5 flex items-center gap-1 text-[10px] font-medium text-theme-yellow transition-colors hover:text-theme-yellow/70"
            >
              <ArrowRight className="size-3" />
              View all advisees in chat
            </button>
          </div>

          {/* Calendar — prompt shortcut; full booking UI activates when Backend M3 ships */}
          <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <Clock className="size-3.5 text-theme-yellow" />
              Calendar
            </h2>
            <div className="flex items-center justify-between rounded-xl bg-theme-gray-light/40 px-4 py-2.5">
              <span className="text-xs text-neutral-400">
                Book a meeting or set a reminder
              </span>
              <button
                type="button"
                onClick={() =>
                  onSelectPrompt("Set a reminder for my next department meeting")
                }
                className="text-[10px] font-medium text-theme-yellow transition-colors hover:text-theme-yellow/70"
              >
                Ask AURA →
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Prompts */}
      <div className="mt-8">
        <h3 className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => onSelectPrompt(prompt)}
              className="flex items-center justify-between rounded-xl border border-theme-gray-light bg-theme-gray/60 px-4 py-2.5 text-left text-xs text-neutral-300 transition-all hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100 group"
            >
              <span>{prompt}</span>
              <ArrowRight className="size-3.5 opacity-0 transition-opacity group-hover:opacity-100 text-theme-yellow" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}