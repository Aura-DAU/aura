"use client"

import React, { useState, useEffect, useCallback } from "react"
import { Shield, Plus, Trash2, Loader2, AlertCircle, UserPlus } from "lucide-react"
import { getErrorMessage, toastError, toastSuccess } from "@/lib/toast"

interface AdminUser {
  email: string
  erp_id: string
  dept: string | null
  created_at: string | null
  has_admin_staff_binding: boolean
}

export function AdminAccessManager() {
  const [admins, setAdmins] = useState<AdminUser[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [email, setEmail] = useState("")
  const [erpId, setErpId] = useState("")
  const [submitting, setSubmitting] = useState(false)
  const [revokingEmail, setRevokingEmail] = useState<string | null>(null)

  const fetchAdmins = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch("/api/admin/users/access")
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.error || "Failed to fetch admin users")
      }
      const data = await res.json()
      setAdmins(data.admins || [])
    } catch (err) {
      const msg = getErrorMessage(err, "Failed to load admin users.")
      setError(msg)
      toastError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchAdmins()
  }, [fetchAdmins])

  const handleGrant = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email.trim()) return

    setSubmitting(true)
    setError(null)

    try {
      const body: { email: string; erp_id?: string } = { email: email.trim().toLowerCase() }
      if (erpId.trim()) {
        body.erp_id = erpId.trim()
      }

      const res = await fetch("/api/admin/users/access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || "Failed to grant admin access")
      }

      toastSuccess(`Admin access granted to ${body.email}. They must sign out and sign back in.`)
      setEmail("")
      setErpId("")
      await fetchAdmins()
    } catch (err) {
      const msg = getErrorMessage(err, "Something went wrong.")
      setError(msg)
      toastError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleRevoke = async (targetEmail: string) => {
    setRevokingEmail(targetEmail)
    setError(null)

    try {
      const res = await fetch("/api/admin/users/access", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: targetEmail }),
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || "Failed to revoke admin access")
      }

      toastSuccess(`Admin access revoked for ${targetEmail}`)
      await fetchAdmins()
    } catch (err) {
      const msg = getErrorMessage(err, "Something went wrong.")
      setError(msg)
      toastError(msg)
    } finally {
      setRevokingEmail(null)
    }
  }

  return (
    <div className="mb-6 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-neutral-200 flex items-center gap-2 font-sans">
          <Shield className="size-5 text-theme-red" />
          Dashboard Admin Access
        </h2>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-theme-red/20 bg-theme-red/5 p-3 text-xs text-theme-red mb-4">
          <AlertCircle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="md:col-span-1 rounded-xl border border-theme-gray-light/50 bg-theme-gray-light/20 p-4 h-fit">
          <h3 className="text-sm font-semibold text-neutral-200 mb-4 flex items-center gap-1.5 font-sans">
            <UserPlus className="size-4 text-theme-yellow" />
            Grant Access
          </h3>
          <form onSubmit={handleGrant} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 font-sans">
                Email
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@dau.ac.in"
                required
                className="w-full rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-3 py-2 text-xs text-neutral-100 placeholder:text-neutral-500 outline-none focus:border-theme-red/60"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 font-sans">
                ERP ID (optional)
              </label>
              <input
                type="text"
                value={erpId}
                onChange={(e) => setErpId(e.target.value)}
                placeholder="Required for non-student emails"
                className="w-full rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-3 py-2 text-xs text-neutral-100 placeholder:text-neutral-500 outline-none focus:border-theme-red/60"
              />
              <span className="text-[9px] text-neutral-500 leading-normal font-sans">
                Auto-inferred from student emails like 202401401@dau.ac.in.
              </span>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-theme-red to-theme-yellow py-2 text-xs font-semibold text-black hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {submitting ? <Loader2 className="size-3.5 animate-spin" /> : <Plus className="size-3.5" />}
              Grant Access
            </button>
          </form>
        </div>

        <div className="md:col-span-2 rounded-xl border border-theme-gray-light/50 bg-theme-gray-light/20 p-4">
          <h3 className="text-sm font-semibold text-neutral-200 mb-4 flex items-center gap-1.5 font-sans">
            <Shield className="size-4 text-theme-yellow" />
            Active Admin Users
          </h3>

          {loading ? (
            <div className="flex items-center justify-center py-12 text-neutral-500">
              <Loader2 className="size-6 animate-spin" />
            </div>
          ) : admins.length === 0 ? (
            <div className="text-center py-10 rounded-xl bg-theme-gray-light/20 border border-theme-gray-light">
              <p className="text-xs text-neutral-500 font-sans">No active admin users found.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {admins.map((admin) => (
                <div
                  key={admin.email}
                  className="flex items-center justify-between rounded-xl bg-theme-gray-light/40 border border-theme-gray-light/60 px-4 py-3.5"
                >
                  <div className="min-w-0 flex-1 flex flex-col gap-1">
                    <span className="text-xs font-semibold text-neutral-200 truncate">
                      {admin.email}
                    </span>
                    <div className="flex flex-wrap items-center gap-3 text-[10px] text-neutral-500 font-sans">
                      <span className="font-mono">ERP: {admin.erp_id}</span>
                      {admin.dept && <span>Dept: {admin.dept}</span>}
                      {admin.has_admin_staff_binding && (
                        <span className="text-theme-yellow">admin_staff binding</span>
                      )}
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRevoke(admin.email)}
                    disabled={revokingEmail === admin.email}
                    aria-label={`Revoke admin access for ${admin.email}`}
                    className="ml-4 shrink-0 rounded-lg p-2 text-neutral-500 hover:bg-theme-red/10 hover:text-theme-red transition-all disabled:opacity-50"
                  >
                    {revokingEmail === admin.email ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Trash2 className="size-4" />
                    )}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
