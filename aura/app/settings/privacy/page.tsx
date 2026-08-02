"use client"

import { useState, useEffect, useRef } from "react"
import { useSession } from "next-auth/react"
import { Loader2, ShieldAlert, UserCheck, UserX, ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"

export default function PrivacySettingsPage() {
  const { status } = useSession()
  const router = useRouter()

  const [advisors, setAdvisors] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [toggling, setToggling] = useState<string | null>(null)
  const loadTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const toggleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login")
      return
    }
    if (status !== "authenticated") return

    loadTimerRef.current = setTimeout(() => {
      setAdvisors(["EMP1001", "EMP1002"])
      setLoading(false)
    }, 600)

    return () => {
      if (loadTimerRef.current) clearTimeout(loadTimerRef.current)
    }
  }, [status, router])

  useEffect(() => {
    return () => {
      if (toggleTimerRef.current) clearTimeout(toggleTimerRef.current)
    }
  }, [])

  if (status === "loading" || loading) {
    return (
      <div className="flex justify-center p-10">
        <Loader2 className="animate-spin text-theme-yellow" />
      </div>
    )
  }

  const toggleAdvisor = async (advisorId: string, currentAccess: boolean) => {
    setToggling(advisorId)
    console.log(
      `[DUMMY] ${currentAccess ? "Revoking" : "Granting"} access for advisor ${advisorId}`
    )

    if (toggleTimerRef.current) clearTimeout(toggleTimerRef.current)
    toggleTimerRef.current = setTimeout(() => {
      setAdvisors((prev) =>
        currentAccess ? prev.filter((id) => id !== advisorId) : [...prev, advisorId]
      )
      setToggling(null)
    }, 500)
  }

  return (
    <div className="relative min-h-screen bg-theme-black px-4 py-10 sm:px-6 lg:px-8 text-neutral-100">
      {/* Background decoration */}
      <div className="pointer-events-none absolute inset-0">
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
          <span className="font-mono text-xs text-neutral-500">PRIVACY</span>
        </div>

        {/* Header */}
        <div className="mb-8">
          <h1 className="flex items-center gap-2.5 text-2xl font-black tracking-tight text-neutral-100 sm:text-3xl lg:text-4xl">
            <ShieldAlert className="size-7 sm:size-8 text-theme-yellow" />
            Privacy &amp; Data Sharing
          </h1>
          <p className="mt-2 text-sm sm:text-base leading-relaxed text-neutral-400">
            Manage which faculty members can access your academic snapshot and attendance data via AURA.
          </p>
        </div>

        <div className="bg-theme-gray/50 border border-theme-gray-light rounded-2xl p-6 backdrop-blur-xl">
          <h2 className="text-lg font-semibold text-neutral-200 mb-4">Faculty Access</h2>

          <div className="space-y-4">
          {[
            { id: "EMP1001", name: "Dr. A. Sharma", role: "Class Advisor" },
            { id: "EMP1002", name: "Prof. B. Patel", role: "Project Guide" },
            { id: "EMP1003", name: "Dr. C. Desai", role: "HOD ICT" },
          ].map((faculty) => {
            const hasAccess = advisors.includes(faculty.id)
            const isToggling = toggling === faculty.id

            return (
              <div
                key={faculty.id}
                className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-xl border border-theme-gray-lighter bg-theme-gray"
              >
                <div>
                  <p className="text-sm sm:text-base font-medium text-neutral-100">{faculty.name}</p>
                  <p className="text-xs sm:text-sm text-neutral-400">
                    {faculty.role} • {faculty.id}
                  </p>
                </div>

                <button
                  type="button"
                  aria-pressed={hasAccess}
                  onClick={() => toggleAdvisor(faculty.id, hasAccess)}
                  disabled={isToggling}
                  className={`flex items-center justify-center sm:justify-start gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${
                    hasAccess
                      ? "bg-theme-red/10 text-theme-red hover:bg-theme-red/20"
                      : "bg-green-500/10 text-green-500 hover:bg-green-500/20"
                  }`}
                >
                  {isToggling ? (
                    <Loader2 className="size-3 animate-spin" />
                  ) : hasAccess ? (
                    <>
                      <UserX className="size-3" /> Revoke Access
                    </>
                  ) : (
                    <>
                      <UserCheck className="size-3" /> Grant Access
                    </>
                  )}
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
