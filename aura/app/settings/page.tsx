"use client"

import Link from "next/link"
import { useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Settings,
  Unlink,
} from "lucide-react"
import { useGoogleCalendarSync } from "@/hooks/use-google-calendar-sync"

function GoogleCalendarCard() {
  const { status, lastSync, error, connect, sync, disconnect } = useGoogleCalendarSync()

  return (
    <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
      <div className="flex items-start gap-4">
        <span className="inline-flex size-10 shrink-0 items-center justify-center rounded-xl bg-theme-yellow/10 text-theme-yellow">
          <CalendarDays className="size-5" />
        </span>
        <div className="min-w-0 flex-1">
          <span className="block text-sm font-semibold text-neutral-100">
            Connect Google Calendar
          </span>
          <span className="mt-1 block text-xs leading-relaxed text-neutral-400">
            Sync your AURA timetable to Google Calendar as recurring weekly events, with
            reminders before every class — kept up to date every time your schedule changes.
          </span>

          <div className="mt-4">
            {status === "loading" ? (
              <span className="inline-flex items-center gap-1.5 text-xs text-neutral-500">
                <Loader2 className="size-3.5 animate-spin" /> Checking connection…
              </span>
            ) : status === "not_connected" ? (
              <button
                type="button"
                onClick={connect}
                className="inline-flex items-center gap-1.5 rounded-xl bg-theme-yellow px-4 py-2 text-xs font-semibold text-theme-black transition-opacity hover:opacity-90"
              >
                <CalendarDays className="size-3.5" />
                Connect Google Calendar
              </button>
            ) : (
              <div className="space-y-3">
                <span className="inline-flex items-center gap-1.5 rounded-full border border-green-500/20 bg-green-500/10 px-3 py-1.5 text-[11px] font-medium text-green-400">
                  <CheckCircle2 className="size-3" /> Connected
                </span>

                {lastSync ? (
                  <p className="text-xs text-neutral-500">
                    Last sync: {lastSync.created ?? 0} added, {lastSync.updated ?? 0} updated
                    {typeof lastSync.removed === "number" ? `, ${lastSync.removed} removed` : ""}.
                  </p>
                ) : null}

                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={sync}
                    disabled={status === "syncing"}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-theme-gray-light bg-theme-black/30 px-3 py-1.5 text-xs font-medium text-neutral-200 transition-colors hover:border-theme-gray-lighter hover:text-neutral-100 disabled:opacity-50"
                  >
                    {status === "syncing" ? (
                      <Loader2 className="size-3.5 animate-spin" />
                    ) : (
                      <RefreshCw className="size-3.5" />
                    )}
                    Sync now
                  </button>
                  <button
                    type="button"
                    onClick={disconnect}
                    disabled={status === "syncing"}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-theme-red/20 bg-theme-red/5 px-3 py-1.5 text-xs font-medium text-theme-red transition-colors hover:bg-theme-red/10 disabled:opacity-50"
                  >
                    <Unlink className="size-3.5" />
                    Disconnect
                  </button>
                </div>
              </div>
            )}

            {error ? <p className="mt-3 text-xs text-theme-red">{error}</p> : null}
          </div>
        </div>
      </div>
    </div>
  )
}

export default function SettingsHubPage() {
  const { status } = useSession()
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
          <span className="text-xs font-mono text-neutral-500">AURA SETTINGS</span>
        </div>

        <div className="mb-8">
          <h1 className="flex items-center gap-2.5 text-2xl font-black tracking-tight text-neutral-100 sm:text-3xl">
            <Settings className="size-7 text-theme-yellow" />
            Settings
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-neutral-400">
            Connect your Google Calendar so your timetable stays in sync.
          </p>
        </div>

        <div className="space-y-3">
          <GoogleCalendarCard />

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
