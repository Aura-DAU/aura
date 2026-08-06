"use client"

import { useEffect } from "react"
import { useSession } from "next-auth/react"
import { Loader2, ShieldAlert, ArrowLeft, Clock } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function PrivacySettingsPage() {
  const { status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login")
    }
  }, [status, router])

  if (status === "loading") {
    return (
      <div className="flex justify-center p-10">
        <Loader2 className="animate-spin text-theme-yellow" />
      </div>
    )
  }

  return (
    <div className="relative min-h-screen bg-theme-black px-4 py-10 sm:px-6 lg:px-8 text-neutral-100">
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="absolute -left-32 -top-32 size-96 rounded-full bg-theme-red/10 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 size-96 rounded-full bg-theme-yellow/10 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-xl md:max-w-2xl lg:max-w-3xl">
        <div className="mb-6 flex items-center justify-between">
          <Link
            href="/settings"
            className="inline-flex items-center gap-2 rounded-xl border border-theme-gray-light bg-theme-gray px-4 py-2 text-xs font-semibold text-neutral-300 transition-colors hover:text-white"
          >
            <ArrowLeft className="size-3.5" /> Back to Settings
          </Link>
          <span className="font-mono text-xs text-neutral-500">PRIVACY</span>
        </div>

        <div className="mb-8">
          <h1 className="flex items-center gap-2.5 text-2xl font-black tracking-tight text-neutral-100 sm:text-3xl lg:text-4xl">
            <ShieldAlert className="size-7 sm:size-8 text-theme-yellow" />
            Privacy &amp; Data Sharing
          </h1>
          <p className="mt-2 text-sm sm:text-base leading-relaxed text-neutral-400">
            Manage which faculty members can access your academic snapshot and attendance data via AURA.
          </p>
        </div>

        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/50 p-6 backdrop-blur-xl">
          <div className="flex items-start gap-3">
            <div className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-xl bg-theme-yellow/10 text-theme-yellow">
              <Clock className="size-4" aria-hidden />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-neutral-200">Coming soon</h2>
              <p className="mt-1.5 text-sm leading-relaxed text-neutral-400">
                Faculty access controls are not available yet. Advisor and guide sharing
                will appear here once UniRP privacy APIs are ready — until then, no
                dummy grants are shown or stored.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
