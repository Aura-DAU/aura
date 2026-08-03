"use client"

import Link from "next/link"
import { useEffect } from "react"
import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import {
  ArrowLeft,
  CalendarCheck2,
  CalendarX2,
  CheckCircle2,
  Loader2,
  RefreshCw,
  Unlink,
  AlertTriangle,
} from "lucide-react"
import { useGoogleCalendarSync } from "@/hooks/use-google-calendar-sync"

export default function CalendarSettingsPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const { status: calStatus, lastSync, error, connect, sync, disconnect } =
    useGoogleCalendarSync()

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

  if (session?.user?.role !== "student") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-theme-black p-6 text-neutral-100">
        <div className="w-full max-w-md rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-6 text-center shadow-2xl">
          <AlertTriangle className="mx-auto mb-4 size-12 text-theme-yellow" />
          <h1 className="mb-2 text-xl font-bold">Students Only</h1>
          <p className="mb-6 text-sm text-neutral-400">
            Google Calendar timetable sync is only available for student accounts.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-xl bg-theme-gray px-4 py-2 text-sm text-neutral-200 hover:text-white"
          >
            <ArrowLeft className="size-4" /> Back to Chat
          </Link>
        </div>
      </div>
    )
  }

  const isLoading = calStatus === "loading"
  const isSyncing = calStatus === "syncing"
  const isConnected = calStatus === "connected"
  const isNotConnected = calStatus === "not_connected"

  return (
    <div className="relative min-h-screen bg-theme-black px-4 py-10 sm:px-6 lg:px-8 text-neutral-100">
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="absolute -left-32 -top-32 size-96 rounded-full bg-theme-red/10 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 size-96 rounded-full bg-theme-yellow/10 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-xl md:max-w-2xl lg:max-w-3xl">
        {/* Nav bar */}
        <div className="mb-6 flex items-center justify-between">
          <Link
            href="/settings"
            className="inline-flex items-center gap-2 rounded-xl border border-theme-gray-light bg-theme-gray px-4 py-2 text-xs font-semibold text-neutral-300 transition-colors hover:text-white"
          >
            <ArrowLeft className="size-3.5" /> Back to Settings
          </Link>
          <span className="font-mono text-xs text-neutral-500">GOOGLE CALENDAR</span>
        </div>

        {/* Header */}
        <div className="mb-8">
          <h1 className="flex items-center gap-2.5 text-2xl font-black tracking-tight text-neutral-100 sm:text-3xl lg:text-4xl">
            <CalendarCheck2 className="size-7 sm:size-8 text-theme-yellow" />
            Google Calendar Sync
          </h1>
          <p className="mt-2 text-sm sm:text-base leading-relaxed text-neutral-400">
            Sync your AURA timetable to Google Calendar as recurring weekly events.
            Google Calendar handles reminders on all your devices automatically.
          </p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-6 flex items-start gap-2.5 rounded-xl border border-theme-red/30 bg-theme-red/10 p-3.5 text-xs leading-relaxed text-red-400 shadow-lg">
            <AlertTriangle className="mt-0.5 size-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-10">
            <Loader2 className="size-6 animate-spin text-theme-yellow" />
            <span className="ml-2.5 text-sm text-neutral-400">Checking connection…</span>
          </div>
        )}

        {/* Not connected state */}
        {isNotConnected && (
          <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-6 shadow-2xl backdrop-blur-xl">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex size-12 items-center justify-center rounded-xl bg-neutral-800">
                <CalendarX2 className="size-6 text-neutral-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-neutral-100">Not Connected</p>
                <p className="text-xs text-neutral-500">Your Google Calendar is not linked yet.</p>
              </div>
            </div>

            <div className="mb-6 rounded-xl border border-theme-gray-light bg-theme-black/30 p-4 text-xs leading-relaxed text-neutral-400">
              <p className="mb-1 font-semibold text-neutral-300">What happens when you connect:</p>
              <ul className="ml-3 list-disc space-y-1">
                <li>AURA creates recurring weekly events in your Google Calendar</li>
                <li>Each class gets a title, room, and faculty information</li>
                <li>Google Calendar sends reminders to your phone / laptop automatically</li>
                <li>Re-sync any time your timetable changes</li>
              </ul>
            </div>

            <button
              id="google-calendar-connect-btn"
              type="button"
              onClick={() => void connect()}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-3 text-sm font-bold text-black transition-opacity hover:opacity-90"
            >
              <CalendarCheck2 className="size-4" />
              Connect Google Calendar
            </button>
          </div>
        )}

        {/* Connected / syncing state */}
        {(isConnected || isSyncing) && (
          <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-6 shadow-2xl backdrop-blur-xl">
            <div className="mb-6 flex items-center gap-3">
              <div className="flex size-12 items-center justify-center rounded-xl bg-green-500/10 ring-1 ring-green-500/20">
                <CheckCircle2 className="size-6 text-green-400" />
              </div>
              <div>
                <p className="text-sm font-semibold text-neutral-100">Calendar Connected</p>
                <p className="text-xs text-neutral-500">
                  {session.user?.email ?? "Your Google account"} is linked.
                </p>
              </div>
            </div>

            {/* Last sync stats */}
            {lastSync && (
              <div className="mb-6 grid grid-cols-3 gap-3">
                {lastSync.created !== undefined && (
                  <div className="rounded-xl border border-theme-gray-light bg-theme-black/30 p-3 text-center">
                    <p className="text-lg font-bold text-theme-yellow">{lastSync.created}</p>
                    <p className="text-[10px] text-neutral-500">Created</p>
                  </div>
                )}
                {lastSync.updated !== undefined && (
                  <div className="rounded-xl border border-theme-gray-light bg-theme-black/30 p-3 text-center">
                    <p className="text-lg font-bold text-neutral-200">{lastSync.updated}</p>
                    <p className="text-[10px] text-neutral-500">Updated</p>
                  </div>
                )}
                {lastSync.removed !== undefined && (
                  <div className="rounded-xl border border-theme-gray-light bg-theme-black/30 p-3 text-center">
                    <p className="text-lg font-bold text-neutral-400">{lastSync.removed}</p>
                    <p className="text-[10px] text-neutral-500">Removed</p>
                  </div>
                )}
              </div>
            )}

            {/* Sync errors */}
            {lastSync?.errors && lastSync.errors.length > 0 && (
              <div className="mb-4 rounded-xl border border-theme-red/30 bg-theme-red/10 p-3">
                <p className="mb-1 text-xs font-semibold text-red-400">Sync warnings</p>
                {lastSync.errors.map((e, i) => (
                  <p key={i} className="text-xs text-neutral-400">{e}</p>
                ))}
              </div>
            )}

            <div className="flex flex-col gap-3">
              {/* Sync button */}
              <button
                id="google-calendar-sync-btn"
                type="button"
                onClick={() => void sync()}
                disabled={isSyncing}
                className="flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-3 text-sm font-bold text-black transition-opacity hover:opacity-90 disabled:opacity-60"
              >
                {isSyncing ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Syncing timetable…
                  </>
                ) : (
                  <>
                    <RefreshCw className="size-4" />
                    Sync Timetable Now
                  </>
                )}
              </button>

              {/* Disconnect button */}
              <button
                id="google-calendar-disconnect-btn"
                type="button"
                onClick={() => void disconnect()}
                disabled={isSyncing}
                className="flex w-full items-center justify-center gap-2 rounded-xl border border-theme-red/30 bg-theme-red/5 py-2.5 text-xs font-semibold text-theme-red transition-all hover:bg-theme-red/10 disabled:opacity-60"
              >
                {isSyncing ? <Loader2 className="size-3.5 animate-spin" /> : <Unlink className="size-3.5" />}
                Disconnect Google Calendar
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
