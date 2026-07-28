"use client"

import React from "react"
import { Calendar, Clock, MapPin, Sparkles, ArrowRight, Bell, BellRing, BellOff, Loader2, Pencil } from "lucide-react"
import { useTimetable, TimetableSlot } from "@/hooks/use-timetable"
import { usePushNotifications } from "@/hooks/use-push-notifications"

interface StudentDashboardProps {
  userName: string
  departmentName?: string
  currentYear?: number
  currentSem?: number
  currentSec?: string
  onSelectPrompt: (text: string) => void
}

const SESSION_TYPE_STYLES: Record<TimetableSlot["session_type"], string> = {
  lecture: "bg-theme-yellow/10 text-theme-yellow border-theme-yellow/20",
  lab: "bg-theme-red/10 text-theme-red border-theme-red/20",
  tutorial: "bg-blue-500/10 text-blue-400 border-blue-500/20",
}

function groupByDay(slots: TimetableSlot[]) {
  const groups = new Map<number, TimetableSlot[]>()
  for (const slot of slots) {
    const list = groups.get(slot.day_of_week) ?? []
    list.push(slot)
    groups.set(slot.day_of_week, list)
  }
  return [...groups.entries()].sort((a, b) => a[0] - b[0])
}

function NotificationToggle() {
  const { status, pending, subscribe, unsubscribe } = usePushNotifications()

  if (status === "unsupported") return null

  if (pending === "subscribe") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray/60 px-3 py-1.5 text-[11px] text-neutral-400">
        <Loader2 className="size-3 animate-spin" /> Enabling…
      </span>
    )
  }

  if (pending === "unsubscribe") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray/60 px-3 py-1.5 text-[11px] text-neutral-400">
        <Loader2 className="size-3 animate-spin" /> Turning off…
      </span>
    )
  }

  if (status === "loading") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray/60 px-3 py-1.5 text-[11px] text-neutral-400">
        <Loader2 className="size-3 animate-spin" /> Checking notifications…
      </span>
    )
  }

  if (status === "denied") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray/60 px-3 py-1.5 text-[11px] text-neutral-500">
        <BellOff className="size-3" /> Notifications blocked in browser settings
      </span>
    )
  }

  if (status === "subscribed") {
    return (
      <button
        type="button"
        onClick={unsubscribe}
        disabled={pending !== null}
        className="inline-flex items-center gap-1.5 rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1.5 text-[11px] font-medium text-green-400 hover:bg-green-500/20 transition-colors disabled:opacity-50"
      >
        <BellRing className="size-3" /> Class reminders on
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={subscribe}
      disabled={pending !== null}
      className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray/60 px-3 py-1.5 text-[11px] font-medium text-neutral-300 hover:border-theme-yellow/40 hover:text-theme-yellow transition-colors disabled:opacity-50"
    >
      <Bell className="size-3" /> Remind me 10 min before class
    </button>
  )
}

export function StudentDashboard({
  userName,
  departmentName = "Information & Communication Technology",
  currentYear,
  currentSem,
  currentSec,
  onSelectPrompt,
}: StudentDashboardProps) {
  const { data, loading, error, refetch } = useTimetable()

  const quickPrompts = [
    "What's my next class today?",
    "Move my 5 PM class to a different room",
    "Add a new lab session to my timetable",
    "Undo my last timetable change",
  ]

  const cohortLabel = data?.cohort
    ? `Year ${data.cohort.year} · Sem ${data.cohort.sem} · Sec ${data.cohort.sec}`
    : currentYear && currentSem && currentSec
      ? `Year ${currentYear} · Sem ${currentSem} · Sec ${currentSec}`
      : undefined

  const grouped = data ? groupByDay(data.timetable) : []

  return (
    <div className="mx-auto w-full max-w-3xl 2xl:max-w-5xl px-4 py-8 text-left animate-in fade-in slide-in-from-bottom-3 duration-200">
      {/* Welcome banner */}
      <div className="mb-6 rounded-2xl border border-theme-gray-light bg-theme-gray/40 p-6 backdrop-blur-md">
        <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-bold text-transparent md:text-2xl">
          Welcome back, {userName}!
        </h1>
        <p className="mt-1 text-xs text-neutral-400">
          Student · {departmentName}
          {cohortLabel ? ` · ${cohortLabel}` : ""}
        </p>
        <div className="mt-4">
          <NotificationToggle />
        </div>
      </div>

      {/* Timetable */}
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            <Calendar className="size-3.5 text-theme-yellow" />
            My Timetable
          </h2>
          <button
            type="button"
            onClick={() => onSelectPrompt("I want to change something in my timetable")}
            className="inline-flex items-center gap-1 text-[11px] font-medium text-theme-yellow hover:text-theme-red transition-colors"
          >
            <Pencil className="size-3" /> Ask AURA to edit
          </button>
        </div>

        {loading && (
          <div className="flex items-center gap-2 py-8 justify-center text-xs text-neutral-500">
            <Loader2 className="size-4 animate-spin" /> Loading your timetable…
          </div>
        )}

        {!loading && error && (
          <div className="rounded-xl border border-theme-red/20 bg-theme-red/5 p-4 text-xs text-theme-red">
            {error}
            <button type="button" onClick={() => refetch()} className="ml-2 underline underline-offset-2">
              Try again
            </button>
          </div>
        )}

        {!loading && !error && grouped.length === 0 && (
          <p className="py-6 text-center text-xs text-neutral-500">
            No classes on your timetable yet. Once your cohort&apos;s schedule is published, it&apos;ll show up here.
          </p>
        )}

        {!loading && !error && grouped.length > 0 && (
          <div className="space-y-4">
            {grouped.map(([, slots]) => (
              <div key={slots[0].day}>
                <h3 className="mb-2 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
                  {slots[0].day}
                </h3>
                <div className="space-y-2">
                  {slots
                    .slice()
                    .sort((a, b) => a.start_time.localeCompare(b.start_time))
                    .map((slot) => (
                      <div
                        key={slot.id}
                        className="flex flex-col gap-1.5 rounded-xl bg-theme-gray-light/40 p-3 border border-transparent hover:border-theme-gray-light transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-1 text-[10px] text-neutral-400">
                            <Clock className="size-3" />
                            {slot.start_time} – {slot.end_time}
                          </span>
                          <span className={`rounded border px-1.5 py-0.5 text-[9px] font-medium capitalize ${SESSION_TYPE_STYLES[slot.session_type]}`}>
                            {slot.session_type}
                          </span>
                        </div>
                        <span className="text-sm font-medium text-neutral-200">
                          {slot.course_name} {slot.course_code ? `(${slot.course_code})` : ""}
                        </span>
                        {(slot.room || slot.faculty_name) && (
                          <span className="flex items-center gap-1 text-xs text-neutral-500">
                            {slot.room && (
                              <>
                                <MapPin className="size-3" /> {slot.room}
                              </>
                            )}
                            {slot.room && slot.faculty_name && <span className="mx-1">·</span>}
                            {slot.faculty_name}
                          </span>
                        )}
                        {slot.is_custom && (
                          <span className="inline-flex w-fit items-center gap-1 rounded bg-theme-yellow/10 px-1.5 py-0.5 text-[9px] font-medium text-theme-yellow border border-theme-yellow/20">
                            <Sparkles className="size-2.5" /> Personalized by you
                          </span>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Starter prompts */}
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
              className="flex items-center justify-between rounded-xl border border-theme-gray-light bg-theme-gray/60 px-4 py-2.5 text-left text-xs text-neutral-300 hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100 transition-all group"
            >
              <span>{prompt}</span>
              <ArrowRight className="size-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-theme-yellow" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
