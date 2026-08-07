"use client"

import React, { useState, useEffect } from "react"
import { Users, GraduationCap, BookOpen, Loader2, AlertCircle, Clock } from "lucide-react"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"
import { getErrorMessage, toastError } from "@/lib/toast"

interface RoleCounts {
  student: number
  faculty: number
  admin: number
  total: number
}

interface UserStats {
  registered: RoleCounts
  recently_active: RoleCounts
  window_days: number
}

interface StatCardProps {
  label: string
  icon: React.ReactNode
  active: number
  registered: number
  windowDays: number
}

function StatCard({ label, icon, active, registered, windowDays }: StatCardProps) {
  return (
    <div className="rounded-xl bg-theme-gray-light/30 border border-theme-gray-light/50 p-4">
      <div className="flex items-center gap-1.5 text-xs text-neutral-400 mb-1">
        {icon}
        {label}
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-neutral-100">{active}</span>
        <span className="text-[10px] text-neutral-500">active in last {windowDays}d</span>
      </div>
      <div className="mt-2 text-[10px] text-neutral-500">
        of {registered} registered
      </div>
    </div>
  )
}

export function UserActivityStats() {
  const [stats, setStats] = useState<UserStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState(7)

  useEffect(() => {
    async function fetchStats() {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch(`/api/admin/stats/users?days=${days}`)
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.error || "Failed to fetch user stats")
        }
        const data = await res.json()
        setStats(data)
      } catch (err) {
        const msg = getErrorMessage(err, "Failed to load user activity data.")
        setError(msg)
        toastError(msg)
      } finally {
        setLoading(false)
      }
    }
    fetchStats()
  }, [days])

  const chartData = stats
    ? [
        {
          name: "Students",
          registered: stats.registered.student,
          active: stats.recently_active.student,
        },
        {
          name: "Faculty",
          registered: stats.registered.faculty,
          active: stats.recently_active.faculty,
        },
      ]
    : []

  return (
    <div className="mb-6 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-neutral-200 flex items-center gap-2 font-sans">
          <Users className="size-5 text-theme-red" />
          User Activity
        </h2>
        <div className="flex items-center gap-2">
          <Clock className="size-4 text-neutral-500" />
          <select
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="bg-theme-gray-light border border-theme-gray-lighter text-xs text-neutral-300 rounded-lg px-2 py-1 outline-none focus:border-theme-red/50"
          >
            <option value={1}>Last 24 Hours</option>
            <option value={7}>Last 7 Days</option>
            <option value={14}>Last 14 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-theme-red/20 bg-theme-red/5 p-3 text-xs text-theme-red mb-4">
          <AlertCircle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-16 text-neutral-500">
          <Loader2 className="size-6 animate-spin" />
        </div>
      ) : stats ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <StatCard
              label="Students"
              icon={<GraduationCap className="size-3.5 text-theme-yellow" />}
              active={stats.recently_active.student}
              registered={stats.registered.student}
              windowDays={stats.window_days}
            />
            <StatCard
              label="Faculty"
              icon={<BookOpen className="size-3.5 text-theme-yellow" />}
              active={stats.recently_active.faculty}
              registered={stats.registered.faculty}
              windowDays={stats.window_days}
            />
            <StatCard
              label="All Users"
              icon={<Users className="size-3.5 text-theme-yellow" />}
              active={stats.recently_active.total}
              registered={stats.registered.total}
              windowDays={stats.window_days}
            />
          </div>

          <div className="h-65 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis dataKey="name" stroke="#666" tick={{ fill: "#888", fontSize: 12 }} />
                <YAxis stroke="#666" tick={{ fill: "#888", fontSize: 12 }} allowDecimals={false} width={40} />
                <Tooltip
                  cursor={{ fill: "rgba(255,255,255,0.05)" }}
                  contentStyle={{
                    backgroundColor: "#111",
                    border: "1px solid #333",
                    borderRadius: "8px",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px" }} />
                <Bar dataKey="registered" name="Registered" fill="#525252" radius={[4, 4, 0, 0]} barSize={40} />
                <Bar dataKey="active" name={`Active (${stats.window_days}d)`} fill="#e53e3e" radius={[4, 4, 0, 0]} barSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <p className="text-center text-[10px] text-neutral-500 font-sans">
            Activity is measured from personal-data queries in the audit log — users who only ask
            public questions are not counted as active.
          </p>
        </div>
      ) : null}
    </div>
  )
}
