"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { LayoutDashboard, ArrowLeft, Settings, ArrowRight, Eye, EyeOff } from "lucide-react"
import { TimetableCard } from "@/components/features/dashboard/TimetableCard"
import { InstallPromptBanner } from "@/components/features/chat-ui/InstallPromptBanner"

interface StudentAcademicDashboardProps {
  userName: string
  departmentName?: string
}

const QUICK_PROMPTS = [
  "What's my next class today?",
  "Show my full weekly timetable",
  "Which electives am I registered for?",
  "When is the next exam?",
]

/** Student dashboard — shows only the timetable card (Google Calendar-backed). */
export function StudentAcademicDashboard({
  userName,
  departmentName = "Information & Communication Technology",
}: StudentAcademicDashboardProps) {
  const router = useRouter()
  const [showTimetable, setShowTimetable] = useState(true)
  const [isMounted, setIsMounted] = useState(false)
  const [preferredName, setPreferredName] = useState(userName)

  useEffect(() => {
    setIsMounted(true)
    const saved = localStorage.getItem("aura_dashboard_show_timetable")
    if (saved !== null) {
      setShowTimetable(saved === "true")
    }
    try {
      const rawProfile = localStorage.getItem("aura-profile-v2")
      if (rawProfile) {
        const profile = JSON.parse(rawProfile)
        if (profile.name) {
          setPreferredName(profile.name)
        }
      }
    } catch {
      // ignore parse errors
    }
  }, [])

  const handleToggleTimetable = () => {
    const next = !showTimetable
    setShowTimetable(next)
    localStorage.setItem("aura_dashboard_show_timetable", next.toString())
  }

  const handleSelectPrompt = (text: string) => {
    router.push(`/?prompt=${encodeURIComponent(text)}`)
  }

  return (
    <>
      <div className="min-h-screen bg-theme-black px-4 py-8 md:px-8">
        <div className="pointer-events-none fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
          <div className="absolute -left-24 -top-24 size-72 rounded-full bg-theme-red/10 blur-3xl" />
          <div className="absolute -bottom-24 -right-24 size-72 rounded-full bg-theme-yellow/10 blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-3xl">
          {/* Header row */}
          <div className="mb-8 flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <LayoutDashboard className="size-5 text-theme-yellow" />
              <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-semibold text-transparent">
                My Dashboard
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <Link
                href="/settings"
                className="inline-flex items-center gap-1.5 rounded-xl border border-theme-gray-light bg-theme-gray/60 px-3 py-1.5 text-xs font-medium text-neutral-300 transition-colors hover:border-theme-gray-lighter hover:text-neutral-100"
              >
                <Settings className="size-3.5 text-theme-yellow" />
                Settings
              </Link>
              <Link
                href="/"
                className="inline-flex items-center gap-1.5 rounded-xl border border-theme-gray-light bg-theme-gray/60 px-3 py-1.5 text-xs font-medium text-neutral-300 transition-colors hover:border-theme-gray-lighter hover:text-neutral-100"
              >
                <ArrowLeft className="size-3.5" />
                Back to Chat
              </Link>
            </div>
          </div>

          {/* Welcome banner */}
          <div className="mb-6 flex flex-col justify-between gap-4 rounded-2xl border border-theme-gray-light bg-theme-gray/40 p-6 backdrop-blur-md sm:flex-row sm:items-center">
            <div>
              <h2 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-bold text-transparent md:text-2xl">
                Welcome back, {preferredName}!
              </h2>
              <p className="mt-1 text-xs text-neutral-400">
                Student · {departmentName}
              </p>
            </div>
            
            {isMounted && (
              <button
                onClick={handleToggleTimetable}
                className="inline-flex items-center gap-1.5 self-start rounded-xl border border-theme-gray-light bg-theme-gray/40 px-3 py-1.5 text-xs font-medium text-neutral-300 transition-colors hover:border-theme-gray-lighter hover:bg-theme-gray/60 hover:text-neutral-100 sm:self-auto"
                title={showTimetable ? "Hide Timetable" : "Show Timetable"}
              >
                {showTimetable ? (
                  <>
                    <EyeOff className="size-3.5" />
                    Hide Timetable
                  </>
                ) : (
                  <>
                    <Eye className="size-3.5 text-theme-yellow" />
                    Show Timetable
                  </>
                )}
              </button>
            )}
          </div>

          {/* Timetable — full width */}
          {(!isMounted || showTimetable) && (
            <TimetableCard />
          )}

          {/* Quick actions */}
          <div className="mt-8">
            <h3 className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
              Quick Actions
            </h3>
            <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
              {QUICK_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => handleSelectPrompt(prompt)}
                  className="group flex items-center justify-between rounded-xl border border-theme-gray-light bg-theme-gray/60 px-4 py-2.5 text-left text-xs text-neutral-300 transition-all hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100"
                >
                  <span>{prompt}</span>
                  <ArrowRight className="size-3.5 text-theme-yellow opacity-0 transition-opacity group-hover:opacity-100" />
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
      <InstallPromptBanner />
    </>
  )
}

