"use client"

import React, { useState, useEffect } from "react"
import { Search, Plus, Trash2, Shield, Calendar, Loader2, CheckCircle2, AlertCircle, Activity, Clock } from "lucide-react"
import { ComposedChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"

interface Binding {
  id: string
  binding: string
  granted_at: string
  expires_at: string | null
  revoked: boolean
}

interface LatencySegment {
  name: string
  min: number
  q1: number
  median: number
  q3: number
  max: number
  mean: number
  count: number
}

interface LatencyStats {
  segments: LatencySegment[]
  total_requests: number
}

interface BoxShapeProps {
  x: number
  y: number
  width: number
  height: number
  fill?: string
  payload: LatencySegment
}

const BoxShape = (props: BoxShapeProps) => {
  const { x, y, width, height, payload, fill } = props
  const { min, q1, median, q3, max } = payload

  const valueRange = q3 - q1
  // If box height is 0 or extremely small, we still want to render whiskers if min/max exist
  const scale = valueRange > 0 ? height / valueRange : 0

  const q3Y = y
  const q1Y = y + height
  const medianY = valueRange > 0 ? q3Y + (q3 - median) * scale : y
  const maxY = valueRange > 0 ? q3Y - (max - q3) * scale : y - 10
  const minY = valueRange > 0 ? q1Y + (q1 - min) * scale : y + 10
  const centerX = x + width / 2

  return (
    <g>
      {/* Whiskers */}
      <line x1={centerX} y1={q3Y} x2={centerX} y2={maxY} stroke={fill} strokeWidth={2} />
      <line x1={x + width * 0.25} y1={maxY} x2={x + width * 0.75} y2={maxY} stroke={fill} strokeWidth={2} />
      
      <line x1={centerX} y1={q1Y} x2={centerX} y2={minY} stroke={fill} strokeWidth={2} />
      <line x1={x + width * 0.25} y1={minY} x2={x + width * 0.75} y2={minY} stroke={fill} strokeWidth={2} />

      {/* IQR Box */}
      <rect x={x} y={q3Y} width={width} height={Math.max(height, 2)} fill={fill} fillOpacity={0.4} stroke={fill} strokeWidth={1} />
      
      {/* Median */}
      <line x1={x} y1={medianY} x2={x + width} y2={medianY} stroke="#fff" strokeWidth={2} />
    </g>
  )
}

export default function AdminBindingsClient() {
  const [erpId, setErpId] = useState("")
  const [searchQuery, setSearchQuery] = useState("")
  const [loading, setLoading] = useState(false)
  const [bindings, setBindings] = useState<Binding[]>([])
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Form state
  const [newBinding, setNewBinding] = useState("")
  const [expiresAt, setExpiresAt] = useState("")
  const [submitting, setSubmitting] = useState(false)

  // Latency Dashboard state
  const [latencyStats, setLatencyStats] = useState<LatencyStats | null>(null)
  const [latencyLoading, setLatencyLoading] = useState(false)
  const [latencyError, setLatencyError] = useState<string | null>(null)
  const [latencyHours, setLatencyHours] = useState(24)

  useEffect(() => {
    async function fetchLatency() {
      setLatencyLoading(true)
      setLatencyError(null)
      try {
        const res = await fetch(`/api/admin/latency?hours=${latencyHours}`)
        if (!res.ok) {
          const errData = await res.json()
          throw new Error(errData.error || "Failed to fetch latency stats")
        }
        const data = await res.json()
        setLatencyStats(data)
      } catch (err) {
        setLatencyError(err instanceof Error ? err.message : "Failed to load latency data.")
      } finally {
        setLatencyLoading(false)
      }
    }
    fetchLatency()
  }, [latencyHours])

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!searchQuery.trim()) return

    setLoading(true)
    setError(null)
    setSuccess(null)
    setErpId(searchQuery.trim())

    try {
      const res = await fetch(`/api/admin/users/${searchQuery.trim()}/bindings`)
      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || "Failed to fetch bindings")
      }
      setBindings(data.bindings || [])
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong."
      setError(msg)
      setBindings([])
    } finally {
      setLoading(false)
    }
  }

  const handleAddBinding = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newBinding.trim() || !erpId) return

    setSubmitting(true)
    setError(null)
    setSuccess(null)

    try {
      const res = await fetch(`/api/admin/users/${erpId}/bindings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          binding: newBinding.trim(),
          expires_at: expiresAt || null,
        }),
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || "Failed to add binding")
      }

      setSuccess(`Binding '${newBinding}' successfully added!`)
      setNewBinding("")
      setExpiresAt("")
      
      // Refresh list
      const refreshRes = await fetch(`/api/admin/users/${erpId}/bindings`)
      const refreshData = await refreshRes.json()
      setBindings(refreshData.bindings || [])
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong."
      setError(msg)
    } finally {
      setSubmitting(false)
    }
  }

  const handleRevokeBinding = async (bindingId: string, bindingName: string) => {
    setError(null)
    setSuccess(null)

    try {
      const res = await fetch(`/api/admin/bindings/${bindingId}`, {
        method: "DELETE",
      })

      const data = await res.json()
      if (!res.ok) {
        throw new Error(data.error || "Failed to revoke binding")
      }

      setSuccess(`Binding '${bindingName}' successfully revoked!`)
      
      // Refresh list
      const refreshRes = await fetch(`/api/admin/users/${erpId}/bindings`)
      const refreshData = await refreshRes.json()
      setBindings(refreshData.bindings || [])
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Something went wrong."
      setError(msg)
    }
  }

  return (
    <div className="min-h-screen bg-theme-black text-neutral-100 px-4 py-12 md:px-8 font-sans">
      <div className="mx-auto max-w-4xl animate-in fade-in duration-200 text-left">
        {/* Header */}
        <div className="mb-8 flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-theme-red/10 border border-theme-red/20 text-theme-red">
            <Shield className="size-5" />
          </div>
          <div>
            <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-bold text-transparent md:text-2xl">
              Admin Dashboard
            </h1>
            <p className="text-xs text-neutral-400 mt-0.5 font-sans">
              Manage scope bindings and monitor system latency metrics.
            </p>
          </div>
        </div>

        {/* Search Card */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 mb-6">
          <form onSubmit={handleSearch} className="flex gap-2.5">
            <div className="relative flex-1">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-neutral-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search user by ERP ID (e.g. 202101001, FAC001)..."
                className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light pl-10 pr-4 py-2.5 text-sm text-neutral-100 placeholder:text-neutral-500 outline-none transition-colors focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow px-6 py-2.5 text-sm font-semibold text-black hover:opacity-90 disabled:opacity-50 transition-opacity"
            >
              {loading ? <Loader2 className="size-4 animate-spin" /> : "Lookup"}
            </button>
          </form>

          {/* Feedback alerts */}
          {error && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-theme-red/20 bg-theme-red/5 p-3 text-xs text-theme-red">
              <AlertCircle className="size-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {success && (
            <div className="mt-4 flex items-center gap-2 rounded-xl border border-green-500/20 bg-green-500/5 p-3 text-xs text-green-400">
              <CheckCircle2 className="size-4 shrink-0" />
              <span>{success}</span>
            </div>
          )}
        </div>

        {erpId && !loading && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {/* Left side: Add Binding Form */}
            <div className="md:col-span-1 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 h-fit">
              <h2 className="text-sm font-semibold text-neutral-200 mb-4 flex items-center gap-1.5 font-sans">
                <Plus className="size-4 text-theme-yellow" />
                Grant Scope
              </h2>
              <form onSubmit={handleAddBinding} className="flex flex-col gap-4">
                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 font-sans">
                    Binding String
                  </label>
                  <input
                    type="text"
                    value={newBinding}
                    onChange={(e) => setNewBinding(e.target.value)}
                    placeholder="e.g. class_advisor:2024_btech_ict"
                    required
                    className="w-full rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-3 py-2 text-xs text-neutral-100 placeholder:text-neutral-500 outline-none focus:border-theme-red/60"
                  />
                  <span className="text-[9px] text-neutral-500 mt-1 leading-normal font-sans">
                    Valid prefixes: class_advisor:, course_instructor:, dean_of_students, exam_committee, admin_full
                  </span>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500 font-sans">
                    Expiration Date
                  </label>
                  <input
                    type="datetime-local"
                    value={expiresAt}
                    onChange={(e) => setExpiresAt(e.target.value)}
                    className="w-full rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-3 py-2 text-xs text-neutral-100 outline-none focus:border-theme-red/60"
                  />
                  <span className="text-[9px] text-neutral-500 leading-normal font-sans">
                    Leave empty for permanent bindings.
                  </span>
                </div>

                <button
                  type="submit"
                  disabled={submitting}
                  className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-theme-gray-light border border-theme-gray-lighter py-2 text-xs font-medium hover:bg-neutral-800 disabled:opacity-50 transition-colors font-sans"
                >
                  {submitting ? <Loader2 className="size-3.5 animate-spin" /> : "Grant Binding"}
                </button>
              </form>
            </div>

            {/* Right side: Active Bindings list */}
            <div className="md:col-span-2 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
              <h2 className="text-sm font-semibold text-neutral-200 mb-4 flex items-center gap-1.5 font-sans">
                <Shield className="size-4 text-theme-yellow" />
                Active Bindings (ERP: {erpId})
              </h2>

              {bindings.length === 0 ? (
                <div className="text-center py-10 rounded-xl bg-theme-gray-light/20 border border-theme-gray-light">
                  <p className="text-xs text-neutral-500 font-sans">No active bindings found for this user.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {bindings.map((b) => (
                    <div
                      key={b.id}
                      className={`flex items-center justify-between rounded-xl bg-theme-gray-light/40 border px-4 py-3.5 ${
                        b.revoked ? "border-theme-red/10 opacity-50" : "border-theme-gray-light/60"
                      }`}
                    >
                      <div className="min-w-0 flex-1 flex flex-col gap-1">
                        <span className="font-mono text-xs font-semibold text-neutral-200 truncate">
                          {b.binding}
                        </span>
                        <div className="flex flex-wrap items-center gap-3 text-[10px] text-neutral-500 font-sans">
                          <span>Granted: {new Date(b.granted_at).toLocaleDateString()}</span>
                          {b.expires_at && (
                            <span className="flex items-center gap-1 text-theme-yellow">
                              <Calendar className="size-2.5" />
                              Expires: {new Date(b.expires_at).toLocaleDateString()}
                            </span>
                          )}
                          {b.revoked && (
                            <span className="text-theme-red font-medium">Revoked</span>
                          )}
                        </div>
                      </div>
                      {!b.revoked && (
                        <button
                          type="button"
                          onClick={() => handleRevokeBinding(b.id, b.binding)}
                          aria-label={`Revoke ${b.binding}`}
                          className="ml-4 shrink-0 rounded-lg p-2 text-neutral-500 hover:bg-theme-red/10 hover:text-theme-red transition-all"
                        >
                          <Trash2 className="size-4" />
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Latency Dashboard Section */}
        <div className="mt-8 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-neutral-200 flex items-center gap-2 font-sans">
              <Activity className="size-5 text-theme-red" />
              System Latency Metrics
            </h2>
            <div className="flex items-center gap-2">
              <Clock className="size-4 text-neutral-500" />
              <select
                value={latencyHours}
                onChange={(e) => setLatencyHours(Number(e.target.value))}
                className="bg-theme-gray-light border border-theme-gray-lighter text-xs text-neutral-300 rounded-lg px-2 py-1 outline-none focus:border-theme-red/50"
              >
                <option value={1}>Last 1 Hour</option>
                <option value={12}>Last 12 Hours</option>
                <option value={24}>Last 24 Hours</option>
                <option value={168}>Last 7 Days</option>
                <option value={720}>Last 30 Days</option>
              </select>
            </div>
          </div>

          {latencyError && (
            <div className="flex items-center gap-2 rounded-xl border border-theme-red/20 bg-theme-red/5 p-3 text-xs text-theme-red mb-4">
              <AlertCircle className="size-4 shrink-0" />
              <span>{latencyError}</span>
            </div>
          )}

          {latencyLoading ? (
            <div className="flex items-center justify-center py-20 text-neutral-500">
              <Loader2 className="size-6 animate-spin" />
            </div>
          ) : latencyStats && latencyStats.total_requests > 0 ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {latencyStats.segments.map((seg) => (
                  <div key={seg.name} className="rounded-xl bg-theme-gray-light/30 border border-theme-gray-light/50 p-4">
                    <div className="text-xs text-neutral-400 capitalize mb-1">{seg.name} Latency</div>
                    <div className="flex items-baseline gap-2">
                      <span className="text-xl font-bold text-neutral-100">{seg.median.toFixed(2)}s</span>
                      <span className="text-[10px] text-neutral-500">median</span>
                    </div>
                    <div className="mt-2 text-[10px] text-neutral-500 flex justify-between">
                      <span>Max: {seg.max.toFixed(2)}s</span>
                      <span>Mean: {seg.mean.toFixed(2)}s</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="h-[400px] w-full pt-4">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart
                    data={latencyStats.segments.map(s => ({
                      ...s,
                      box: [s.q1, s.q3],
                    }))}
                    margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis dataKey="name" stroke="#666" tick={{ fill: '#888', fontSize: 12 }} textAnchor="middle" />
                    <YAxis
                      stroke="#666"
                      tick={{ fill: '#888', fontSize: 12 }}
                      unit="s"
                      width={40}
                    />
                    <Tooltip
                      cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload as LatencySegment
                          return (
                            <div className="bg-theme-black border border-theme-gray-light p-3 rounded-lg shadow-xl text-xs space-y-1">
                              <div className="font-semibold text-neutral-200 capitalize mb-2 border-b border-theme-gray-light pb-1">
                                {data.name} Phase
                              </div>
                              <div className="flex justify-between gap-4"><span className="text-neutral-400">Max:</span> <span className="text-theme-red font-mono">{data.max.toFixed(3)}s</span></div>
                              <div className="flex justify-between gap-4"><span className="text-neutral-400">Q3 (75%):</span> <span className="text-neutral-200 font-mono">{data.q3.toFixed(3)}s</span></div>
                              <div className="flex justify-between gap-4"><span className="text-neutral-400">Median:</span> <span className="text-theme-yellow font-mono">{data.median.toFixed(3)}s</span></div>
                              <div className="flex justify-between gap-4"><span className="text-neutral-400">Q1 (25%):</span> <span className="text-neutral-200 font-mono">{data.q1.toFixed(3)}s</span></div>
                              <div className="flex justify-between gap-4"><span className="text-neutral-400">Min:</span> <span className="text-neutral-500 font-mono">{data.min.toFixed(3)}s</span></div>
                              <div className="border-t border-theme-gray-light mt-2 pt-1 flex justify-between gap-4">
                                <span className="text-neutral-400">Mean:</span> <span className="text-neutral-300 font-mono">{data.mean.toFixed(3)}s</span>
                              </div>
                            </div>
                          )
                        }
                        return null
                      }}
                    />
                    <Bar
                      dataKey="box"
                      fill="#e53e3e"
                      shape={(props: any) => <BoxShape {...props} />}
                      barSize={40}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
              <div className="text-center text-[10px] text-neutral-500 font-sans">
                Based on {latencyStats.total_requests} requests
              </div>
            </div>
          ) : (
            <div className="text-center py-10 rounded-xl bg-theme-gray-light/20 border border-theme-gray-light">
              <p className="text-xs text-neutral-500 font-sans">No latency data available for the selected time range.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
