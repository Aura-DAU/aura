"use client"

import { useState, useEffect, useRef } from "react"
import { useSession } from "next-auth/react"
import { Loader2, ShieldAlert, UserCheck, UserX } from "lucide-react"
import { useRouter } from "next/navigation"

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
    <div className="max-w-2xl mx-auto p-6 mt-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-neutral-100 flex items-center gap-2">
          <ShieldAlert className="text-theme-red" />
          Privacy & Data Sharing
        </h1>
        <p className="text-neutral-400 mt-2 text-sm">
          Manage which faculty members can access your academic snapshot and attendance data via AURA.
        </p>
      </div>

      <div className="bg-theme-gray/50 border border-theme-gray-light rounded-xl p-6">
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
                className="flex items-center justify-between p-4 rounded-lg border border-theme-gray-lighter bg-theme-gray"
              >
                <div>
                  <p className="text-sm font-medium text-neutral-100">{faculty.name}</p>
                  <p className="text-xs text-neutral-400">
                    {faculty.role} • {faculty.id}
                  </p>
                </div>

                <button
                  type="button"
                  aria-pressed={hasAccess}
                  onClick={() => toggleAdvisor(faculty.id, hasAccess)}
                  disabled={isToggling}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-semibold transition-colors ${
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
