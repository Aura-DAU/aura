"use client"

import { useState } from "react"
import { useSession } from "next-auth/react"
import { Loader2, KeyRound, AlertTriangle, ShieldCheck } from "lucide-react"
import { useRouter } from "next/navigation"

export default function ConnectEcampusPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  if (status === "loading") {
    return <div className="flex justify-center p-10"><Loader2 className="animate-spin text-theme-yellow" /></div>
  }

  if (status === "unauthenticated") {
    router.push("/login")
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const res = await fetch("/api/ecampus/connect", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      })

      const data = await res.json()
      
      if (!res.ok) {
        setError(data.error || "Failed to connect")
      } else {
        setSuccess(true)
        setPassword("")
      }
    } catch (err) {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-xl mx-auto p-6 mt-10">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-neutral-100 flex items-center gap-2">
          <KeyRound className="text-theme-red" />
          Connect eCampus Account
        </h1>
        <p className="text-neutral-400 mt-2 text-sm">
          AURA needs access to your eCampus portal to fetch your academic snapshot, attendance, and exam eligibility.
        </p>
      </div>

      {success ? (
        <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-6 text-center">
          <ShieldCheck className="size-10 text-green-500 mx-auto mb-3" />
          <h2 className="text-lg font-semibold text-green-400">Account Connected</h2>
          <p className="text-sm text-neutral-300 mt-1">
            Your eCampus credentials have been securely vaulted.
          </p>
          <button 
            onClick={() => router.push("/")}
            className="mt-6 px-4 py-2 bg-theme-gray rounded-lg text-sm text-neutral-200 hover:text-white"
          >
            Return to Chat
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-theme-gray/50 border border-theme-gray-light rounded-xl p-6">
          <div className="bg-theme-red/10 border border-theme-red/20 rounded-lg p-4 mb-6 flex gap-3">
            <AlertTriangle className="text-theme-red shrink-0 size-5" />
            <p className="text-xs text-neutral-300 leading-relaxed">
              <strong>Consent Statement:</strong> By providing your password, you consent to AURA securely storing these credentials in an encrypted vault. AURA will use them exclusively to answer your personal data queries via read-only scraping.
            </p>
          </div>

          <div className="flex flex-col gap-1.5 mb-6">
            <label className="text-xs font-medium text-neutral-300">
              eCampus Password (for {session?.user?.erpId || "your ID"})
            </label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3.5 py-2.5 text-sm text-neutral-100 outline-none focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
              required
            />
          </div>

          {error && <p className="text-theme-red text-xs mb-4">{error}</p>}

          <button
            type="submit"
            disabled={loading || !password}
            className="w-full flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-2.5 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-60"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : "Securely Vault Credentials"}
          </button>
        </form>
      )}
    </div>
  )
}
