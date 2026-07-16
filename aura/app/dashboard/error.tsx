"use client"

import { useEffect } from "react"
import { AlertTriangle } from "lucide-react"
import { useRouter } from "next/navigation"

interface ErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

/** Error boundary for the /dashboard route — required by CLAUDE.md. */
export default function DashboardError({ error, reset }: ErrorProps) {
  const router = useRouter()

  useEffect(() => {
    // Log to the console; structured error reporting goes here in prod
    console.error("[dashboard] render error:", error)
  }, [error])

  return (
    <div className="flex min-h-screen items-center justify-center bg-theme-black px-4">
      <div className="max-w-sm rounded-2xl border border-theme-red/30 bg-theme-gray p-8 text-center">
        <AlertTriangle className="mx-auto mb-4 size-8 text-theme-red" />
        <h1 className="mb-2 text-lg font-semibold text-neutral-100">
          Dashboard failed to load
        </h1>
        <p className="mb-6 text-sm text-neutral-400">
          Something went wrong while loading your dashboard. This is usually a temporary issue.
        </p>
        <div className="flex flex-col gap-2 sm:flex-row sm:justify-center">
          <button
            type="button"
            onClick={reset}
            className="rounded-xl bg-theme-red px-4 py-2 text-sm font-semibold text-white transition-opacity hover:opacity-90"
          >
            Try again
          </button>
          <button
            type="button"
            onClick={() => router.push("/")}
            className="rounded-xl border border-theme-gray-light px-4 py-2 text-sm text-neutral-300 transition-colors hover:bg-theme-gray-light"
          >
            Go to chat
          </button>
        </div>
      </div>
    </div>
  )
}
