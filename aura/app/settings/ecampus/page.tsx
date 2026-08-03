"use client"

import { useState, useEffect } from "react"
import { useSession } from "next-auth/react"
import { Loader2, KeyRound, AlertTriangle, ShieldCheck, UserCheck, Trash2, ArrowLeft } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { toastError, toastSuccess } from "@/lib/toast"

export default function ConnectEcampusPage() {
  const { data: session, status } = useSession()
  const router = useRouter()

  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [statusLoading, setStatusLoading] = useState(true)
  const [linked, setLinked] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/login")
    }
  }, [status, router])

  useEffect(() => {
    if (status !== "authenticated") return

    let cancelled = false
    const checkLinkStatus = async () => {
      try {
        const res = await fetch("/api/ecampus/link")
        if (cancelled) return
        if (res.ok) {
          const data = await res.json()
          setLinked(data.linked)
        } else {
          toastError("Could not check eCampus link status.")
        }
      } catch (err) {
        if (!cancelled) {
          console.error("Failed to fetch link status:", err)
          toastError("Could not check eCampus link status.")
        }
      } finally {
        if (!cancelled) setStatusLoading(false)
      }
    }

    void checkLinkStatus()
    if (session?.user?.erpId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setUsername(session.user.erpId)
    }

    return () => {
      cancelled = true
    }
  }, [status, session])

  if (
    status === "loading" ||
    status === "unauthenticated" ||
    (status === "authenticated" && statusLoading)
  ) {
    return (
      <div className="flex h-screen items-center justify-center bg-theme-black">
        <Loader2 className="animate-spin text-theme-yellow size-8" />
      </div>
    )
  }

  // Only students should be able to link accounts
  if (session?.user?.role !== "student") {
    return (
      <div className="min-h-screen bg-theme-black text-neutral-100 flex flex-col items-center justify-center p-6">
        <div className="max-w-md w-full bg-theme-gray/80 border border-theme-gray-light rounded-2xl p-6 text-center shadow-2xl">
          <AlertTriangle className="size-12 text-theme-yellow mx-auto mb-4" />
          <h1 className="text-xl font-bold mb-2">Access Denied</h1>
          <p className="text-sm text-neutral-400 mb-6">
            Only students are required to link an eCampus account. Your role is registered as: <strong className="text-neutral-200 capitalize">{session?.user?.role}</strong>.
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

  // Handle linking credentials (POST)
  const handleLink = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccessMsg(null)
    setLoading(true)

    try {
      const res = await fetch("/api/ecampus/link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ecampus_username: username, ecampus_password: password }),
      })

      const data = await res.json()

      if (!res.ok) {
        const msg = data.error || "Failed to link credentials."
        setError(msg)
        toastError(msg)
      } else {
        setLinked(true)
        const msg = "Your eCampus account has been connected successfully!"
        setSuccessMsg(msg)
        toastSuccess(msg)
        setPassword("")
      }
    } catch {
      const msg = "Network error. Please try again."
      setError(msg)
      toastError(msg)
    } finally {
      setLoading(false)
    }
  }

  // Handle unlinking credentials (DELETE)
  const handleUnlink = async () => {
    if (!confirm("Are you sure you want to unlink your eCampus account? AURA will no longer be able to scrape your personal data.")) {
      return
    }

    setError(null)
    setSuccessMsg(null)
    setLoading(true)

    try {
      const res = await fetch("/api/ecampus/link", {
        method: "DELETE",
      })

      const data = await res.json()

      if (!res.ok) {
        const msg = data.error || "Failed to unlink credentials."
        setError(msg)
        toastError(msg)
      } else {
        setLinked(false)
        const msg = "Your eCampus account has been disconnected."
        setSuccessMsg(msg)
        toastSuccess(msg)
      }
    } catch {
      const msg = "Network error. Please try again."
      setError(msg)
      toastError(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="relative min-h-screen bg-theme-black text-neutral-100 flex flex-col justify-between py-10 px-4 sm:px-6 lg:px-8">
      {/* Background layout decoration */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="absolute -left-32 -top-32 size-96 rounded-full bg-theme-red/10 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 size-96 rounded-full bg-theme-yellow/10 blur-3xl" />
      </div>

      <div className="relative z-10 mx-auto w-full max-w-xl md:max-w-2xl lg:max-w-3xl flex-1 flex flex-col justify-center">
        {/* Navigation Bar */}
        <div className="mb-6 flex justify-between items-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 rounded-xl border border-theme-gray-light bg-theme-gray px-4 py-2 text-xs font-semibold text-neutral-300 transition-colors hover:text-white"
          >
            <ArrowLeft className="size-3.5" /> Back to Chat
          </Link>
          <span className="text-xs font-mono text-neutral-500">AURA SETTINGS</span>
        </div>

        {/* Header Section */}
        <div className="mb-8">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-black tracking-tight text-neutral-100 flex items-center gap-2.5">
            <KeyRound className="text-theme-yellow size-7 sm:size-8" />
            Connect eCampus Account
          </h1>
          <p className="text-neutral-400 mt-2 text-sm sm:text-base leading-relaxed">
            AURA needs to fetch your academic snapshot, timetable, and exam eligibility from the eCampus portal on your behalf.
          </p>
        </div>

        {/* Success Alert */}
        {successMsg && (
          <div className="mb-6 flex items-start gap-2.5 rounded-xl border border-green-500/30 bg-green-500/10 p-3.5 text-xs text-green-400 leading-relaxed shadow-lg">
            <ShieldCheck className="size-4 shrink-0 mt-0.5" />
            <span>{successMsg}</span>
          </div>
        )}

        {/* Main Box */}
        {linked ? (
          /* CONNECTED STATE */
          <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 shadow-2xl backdrop-blur-xl p-6 flex flex-col items-center text-center">
            <div className="size-16 rounded-full bg-green-500/10 border border-green-500/20 flex items-center justify-center mb-4">
              <UserCheck className="size-8 text-green-400" />
            </div>
            <h2 className="text-lg font-bold text-neutral-100">eCampus Account Connected</h2>
            <p className="text-xs text-neutral-400 mt-1.5 max-w-sm leading-relaxed">
              Your credentials are saved securely in an encrypted vault. AURA can retrieve your courses and timetable seamlessly.
            </p>

            <div className="w-full mt-6 border-t border-theme-gray-light pt-6 flex justify-between items-center text-xs">
              <span className="text-neutral-500">Linked ERP ID:</span>
              <span className="font-mono font-bold text-neutral-300">{username}</span>
            </div>

            <button
              onClick={handleUnlink}
              disabled={loading}
              className="mt-6 w-full flex items-center justify-center gap-2 rounded-xl border border-theme-red/30 bg-theme-red/5 hover:bg-theme-red/10 py-2.5 text-xs font-semibold text-theme-red transition-all cursor-pointer disabled:opacity-60"
            >
              {loading ? <Loader2 className="size-3.5 animate-spin" /> : <Trash2 className="size-3.5" />}
              Disconnect eCampus Account
            </button>
          </div>
        ) : (
          /* NOT CONNECTED STATE (LINKING FORM) */
          <form onSubmit={handleLink} className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 shadow-2xl backdrop-blur-xl p-6">
            <div className="bg-theme-red/10 border border-theme-red/20 rounded-xl p-4 mb-6 flex gap-3">
              <AlertTriangle className="text-theme-red shrink-0 size-5 mt-0.5" />
              <div className="text-xs text-neutral-300 leading-relaxed">
                <span className="font-bold text-theme-red block mb-1">Consent Statement:</span>
                By entering your credentials, you consent to AURA storing them in an encrypted vault. AURA uses them solely to login to your eCampus portal in a read-only scraper session to retrieve your personal academic data.
              </div>
            </div>

            {/* Username input */}
            <div className="flex flex-col gap-1.5 mb-4">
              <label className="text-xs font-medium text-neutral-300">
                eCampus Username (ERP ID / Roll Number)
              </label>
              <input
                type="text"
                placeholder="2023XXXXX"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3.5 py-2.5 text-sm text-neutral-100 placeholder:text-neutral-500 outline-none focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
                required
              />
            </div>

            {/* Password input */}
            <div className="flex flex-col gap-1.5 mb-6">
              <label className="text-xs font-medium text-neutral-300">
                eCampus Password
              </label>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3.5 py-2.5 text-sm text-neutral-100 placeholder:text-neutral-500 outline-none focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
                required
              />
            </div>

            {/* Error Message */}
            {error && (
              <p role="alert" className="mb-4 rounded-lg border border-theme-red/30 bg-theme-red/10 px-3 py-2 text-xs text-theme-red leading-normal">
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={loading || !username || !password}
              className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-3 text-sm font-bold text-black transition-opacity hover:opacity-90 disabled:opacity-60 cursor-pointer"
            >
              {loading ? <Loader2 className="size-4 animate-spin" /> : <ShieldCheck className="size-4" />}
              Securely Connect eCampus
            </button>
          </form>
        )}
      </div>

      <p className="mt-8 text-center text-[10px] text-neutral-600">
        🔐 Credentials are encrypted at rest with AES-GCM and never shared with third parties.
      </p>
    </div>
  )
}
