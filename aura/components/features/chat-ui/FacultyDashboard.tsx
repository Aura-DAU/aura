"use client"

import { Calendar, Users, ArrowRight, Clock } from "lucide-react"

interface FacultyDashboardProps {
  userName: string
  onSelectPrompt: (text: string) => void
}

/**
 * Faculty home cards. Live schedule/advisee payloads used to come from two
 * full `/api/chat` RAG streams on mount — slow, quota-heavy, and often soft-
 * failed as "unavailable". Until UniRP faculty routes exist, these cards are
 * prompt shortcuts (same pattern as Calendar below).
 *
 * TODO(unirp): Replace prompt cards with UniRP endpoints when faculty data
 * routes are confirmed. Do NOT reintroduce `/api/chat` streams for widgets.
 */
export function FacultyDashboard({
  userName,
  onSelectPrompt,
}: FacultyDashboardProps) {
  const quickPrompts = [
    "What is the consultancy policy?",
    "How do I apply for a seed grant?",
    "Where can I find the course file template?",
  ]

  return (
    <div className="mx-auto w-full max-w-3xl 2xl:max-w-5xl px-4 py-8 text-left animate-in fade-in slide-in-from-bottom-3 duration-200">
      <div className="mb-6 rounded-2xl border border-theme-gray-light bg-theme-gray/40 p-6 backdrop-blur-md">
        <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-bold text-transparent md:text-2xl">
          Welcome back, Prof. {userName}!
        </h1>
        <p className="mt-1 text-xs text-neutral-400">Faculty</p>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
          <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            <Calendar className="size-3.5 text-theme-yellow" />
            Today&apos;s Schedule
          </h2>
          <div className="flex items-center justify-between gap-3 rounded-xl bg-theme-gray-light/40 px-4 py-2.5">
            <span className="text-xs text-neutral-400">
              Ask AURA for your teaching schedule for today
            </span>
            <button
              type="button"
              onClick={() =>
                onSelectPrompt("What is my teaching schedule for today?")
              }
              className="shrink-0 text-[10px] font-medium text-theme-yellow transition-colors hover:text-theme-yellow/70"
            >
              Ask AURA →
            </button>
          </div>
          <p className="mt-2 text-[10px] leading-relaxed text-neutral-600">
            AURA derives faculty schedule from linked student timetable data.
            Coverage improves as more students connect eCampus.
          </p>
        </div>

        <div className="flex flex-col gap-5">
          <div className="flex-1 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <Users className="size-3.5 text-theme-yellow" />
              Advisees
            </h2>
            <div className="flex items-center justify-between gap-3 rounded-xl bg-theme-gray-light/40 px-4 py-2.5">
              <span className="text-xs text-neutral-400">
                View advisee count and semester details
              </span>
              <button
                type="button"
                onClick={() =>
                  onSelectPrompt(
                    "List all my advisees and their current semester details",
                  )
                }
                className="shrink-0 text-[10px] font-medium text-theme-yellow transition-colors hover:text-theme-yellow/70"
              >
                Ask AURA →
              </button>
            </div>
            <button
              type="button"
              onClick={() =>
                onSelectPrompt(
                  "List all my advisees and their current semester details",
                )
              }
              className="mt-2.5 flex items-center gap-1 text-[10px] font-medium text-theme-yellow transition-colors hover:text-theme-yellow/70"
            >
              <ArrowRight className="size-3" />
              View all advisees in chat
            </button>
          </div>

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
              className="group flex items-center justify-between rounded-xl border border-theme-gray-light bg-theme-gray/60 px-4 py-2.5 text-left text-xs text-neutral-300 transition-all hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100"
            >
              <span>{prompt}</span>
              <ArrowRight className="size-3.5 text-theme-yellow opacity-0 transition-opacity group-hover:opacity-100" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
