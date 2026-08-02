"use client"

import Link from "next/link"
import { useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft,
  CalendarCheck2,
  Loader2,
  ShieldAlert,
  Settings,
} from "lucide-react"

export default function SettingsHubPage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login")
    }
  }, [status, router])

  if (status === "loading" || status === "unauthenticated") {
    return (
      <div className="flex h-screen items-center justify-center bg-theme-black">
        <Loader2 className="size-8 animate-spin text-theme-yellow" />
      </div>
    )
  }

  const isStudent = session?.user?.role === "student"

  return (
    <div className="relative min-h-screen bg-theme-black px-4 py-10 text-neutral-100">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="absolute -left-32 -top-32 size-96 rounded-full bg-theme-red/10 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 size-96 rounded-full bg-theme-yellow/10 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-xl">
        <div className="mb-6 flex items-center justify-between">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-xl border border-theme-gray-light bg-theme-gray px-4 py-2 text-xs font-semibold text-neutral-300 transition-colors hover:text-white"
          >
            <ArrowLeft className="size-3.5" /> Back to Chat
          </Link>
          <span className="font-mono text-xs text-neutral-500">AURA SETTINGS</span>
        </div>

        <div className="mb-8">
          <h1 className="flex items-center gap-2.5 text-2xl font-black tracking-tight text-neutral-100 sm:text-3xl">
            <Settings className="size-7 text-theme-yellow" />
            Settings
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-neutral-400">
            Manage your Google Calendar connection and privacy preferences.
          </p>
        </div>

        <div className="space-y-3">
          {isStudent ? (
            <Link
              href="/settings/calendar"
              className="flex items-start gap-4 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 transition-colors hover:border-theme-gray-lighter hover:bg-theme-gray"
            >
              <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-theme-yellow/10 text-theme-yellow">
                <CalendarCheck2 className="size-5" />
              </span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold text-neutral-100">
                  Connect Google Calendar
                </span>
                <span className="mt-1 block text-xs leading-relaxed text-neutral-400">
                  Link your Google account so AURA can sync your timetable as weekly recurring events with reminders.
                </span>
              </span>
            </Link>
          ) : null}

          <Link
            href="/settings/privacy"
            className="flex items-start gap-4 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 transition-colors hover:border-theme-gray-lighter hover:bg-theme-gray"
          >
            <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-theme-yellow/10 text-theme-yellow">
              <ShieldAlert className="size-5" />
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold text-neutral-100">
                Privacy &amp; Data Sharing
              </span>
              <span className="mt-1 block text-xs leading-relaxed text-neutral-400">
                Control which faculty members can access your academic snapshot.
              </span>
            </span>
          </Link>

          <Link
            href="/dashboard"
            className="flex items-center justify-center gap-2 rounded-xl border border-theme-gray-light bg-theme-black/30 px-4 py-3 text-sm font-medium text-neutral-300 transition-colors hover:border-theme-gray-lighter hover:text-neutral-100"
          >
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  )
}
