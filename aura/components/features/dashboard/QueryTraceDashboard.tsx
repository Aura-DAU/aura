"use client"

import React, { useState, useEffect, useCallback } from "react"
import {
  Search,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  ShieldAlert,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Copy,
  Check,
  X,
  FileText,
  Activity,
  Database,
  User,
  Zap,
  Info,
} from "lucide-react"
import { getErrorMessage, toastError, toastSuccess } from "@/lib/toast"
import { MarkdownContent } from "@/components/ui/markdown-content"

export interface QueryTraceItem {
  id: string
  created_at: string
  erp_id: string | null
  user_role: string | null
  user_dept: string | null
  query_text: string
  query_type: string | null
  status: "passed" | "failed" | "flagged" | "fallback" | string
  failure_stage: string
  failure_reason: string | null
  sources_fetched?: Array<{
    file?: string
    title?: string
    score?: number
    start_line?: number
    end_line?: number
    path?: string
    [key: string]: unknown
  }>
  sources_count: number
  answer_preview: string | null
  latency_total_ms: number | null
  latency_guardrail_ms: number | null
  latency_retrieval_ms: number | null
  latency_generation_ms: number | null
  is_personal_data: boolean
}

export interface QueryStats {
  total_queries: number
  passed_count: number
  failed_count: number
  flagged_count: number
  fallback_count: number
  pass_rate: number
  top_failure_cause: string | null
  failure_breakdown: Array<{
    stage: string
    count: number
    percentage: number
  }>
  status_counts: Record<string, number>
  avg_latency_ms: number
  window_hours: number
}

const STAGE_LABELS: Record<string, string> = {
  safety_guardrail: "Safety Guardrail",
  wellness_guardrail: "Wellness Guardrail",
  strict_guardrail: "Strict Guardrail",
  guest_gate: "Guest Gate",
  access_denied: "Access Control",
  academic_scope_missing: "Academic Scope Missing",
  retrieval_empty: "Retrieval Empty",
  context_length_exceeded: "Context Limit Exceeded",
  vllm_timeout: "vLLM Timeout",
  generation_error: "Generation Error",
  none: "None (Passed)",
}

export function QueryTraceDashboard() {
  // Filters & Pagination state
  const [hours, setHours] = useState<number>(24)
  const [statusFilter, setStatusFilter] = useState<string>("all")
  const [stageFilter, setStageFilter] = useState<string>("all")
  const [searchInput, setSearchInput] = useState<string>("")
  const [debouncedSearch, setDebouncedSearch] = useState<string>("")
  const [page, setPage] = useState<number>(1)
  const [pageSize, setPageSize] = useState<number>(20)

  // Data state
  const [stats, setStats] = useState<QueryStats | null>(null)
  const [items, setItems] = useState<QueryTraceItem[]>([])
  const [totalItems, setTotalItems] = useState<number>(0)
  const [totalPages, setTotalPages] = useState<number>(1)
  const [loading, setLoading] = useState<boolean>(false)
  const [statsLoading, setStatsLoading] = useState<boolean>(false)

  // Drawer state
  const [selectedTrace, setSelectedTrace] = useState<QueryTraceItem | null>(null)
  const [copiedQuery, setCopiedQuery] = useState<boolean>(false)

  // Debounce search input
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchInput.trim())
      setPage(1)
    }, 400)
    return () => clearTimeout(handler)
  }, [searchInput])

  // Fetch KPI Stats
  const fetchStats = useCallback(async () => {
    setStatsLoading(true)
    try {
      const res = await fetch(`/api/admin/queries/stats?hours=${hours}`)
      if (!res.ok) {
        throw new Error("Failed to fetch query statistics")
      }
      const data: QueryStats = await res.json()
      setStats(data)
    } catch (err: unknown) {
      toastError(getErrorMessage(err, "Failed to load query stats"))
    } finally {
      setStatsLoading(false)
    }
  }, [hours])

  // Fetch Query Traces List
  const fetchTraces = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.set("hours", hours.toString())
      params.set("page", page.toString())
      params.set("page_size", pageSize.toString())
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter)
      if (stageFilter && stageFilter !== "all") params.set("stage", stageFilter)
      if (debouncedSearch) params.set("search", debouncedSearch)

      const res = await fetch(`/api/admin/queries?${params.toString()}`)
      if (!res.ok) {
        throw new Error("Failed to fetch query traces")
      }
      const data = await res.json()
      setItems(data.items || [])
      setTotalItems(data.total || 0)
      setTotalPages(data.pages || 1)
    } catch (err: unknown) {
      toastError(getErrorMessage(err, "Failed to load query traces"))
    } finally {
      setLoading(false)
    }
  }, [hours, page, pageSize, statusFilter, stageFilter, debouncedSearch])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchStats()
  }, [fetchStats])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchTraces()
  }, [fetchTraces])

  // Copy query text helper
  const handleCopyQuery = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedQuery(true)
    toastSuccess("Query copied to clipboard")
    setTimeout(() => setCopiedQuery(false), 2000)
  }

  // Format date helper
  const formatDate = (isoString: string) => {
    try {
      const d = new Date(isoString)
      return d.toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })
    } catch {
      return isoString
    }
  }

  return (
    <div className="space-y-6">
      {/* ── 1. KPI Cards ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {/* Total Volume */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:border-theme-gray-lighter">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-neutral-400">Total Queries</span>
            <div className="flex size-8 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400">
              <Activity className="size-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-neutral-100 font-mono">
              {statsLoading ? "—" : stats?.total_queries.toLocaleString() ?? "0"}
            </span>
            <span className="text-xs text-neutral-500">last {hours}h</span>
          </div>
          <div className="mt-2 text-[11px] text-neutral-400 flex gap-2">
            <span>Avg latency: <strong className="text-neutral-200">{stats?.avg_latency_ms ?? 0}ms</strong></span>
          </div>
        </div>

        {/* Pass Rate */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:border-theme-gray-lighter">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-neutral-400">Pass Rate</span>
            <div className="flex size-8 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400">
              <CheckCircle2 className="size-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold font-mono ${
                (stats?.pass_rate ?? 0) >= 90
                  ? "text-emerald-400"
                  : (stats?.pass_rate ?? 0) >= 75
                  ? "text-amber-400"
                  : "text-red-400"
              }`}
            >
              {statsLoading ? "—" : `${stats?.pass_rate ?? 100}%`}
            </span>
            <span className="text-xs text-neutral-500">
              {stats?.passed_count ?? 0} succeeded
            </span>
          </div>
          <div className="mt-2 text-[11px] text-neutral-400">
            <span>Target SLA: &gt; 95%</span>
          </div>
        </div>

        {/* Failed Queries */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:border-theme-gray-lighter">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-neutral-400">Failed Queries</span>
            <div className="flex size-8 items-center justify-center rounded-xl bg-red-500/10 text-red-400">
              <XCircle className="size-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold font-mono ${
                (stats?.failed_count ?? 0) > 0 ? "text-red-400" : "text-neutral-100"
              }`}
            >
              {statsLoading ? "—" : stats?.failed_count.toLocaleString() ?? "0"}
            </span>
            <span className="text-xs text-neutral-500">
              +{stats?.flagged_count ?? 0} flagged
            </span>
          </div>
          <div className="mt-2 text-[11px] text-neutral-400">
            <span>{stats?.fallback_count ?? 0} fallback answers</span>
          </div>
        </div>

        {/* Top Failure Cause */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 shadow-sm backdrop-blur-sm transition-all hover:border-theme-gray-lighter">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-neutral-400">Top Failure Cause</span>
            <div className="flex size-8 items-center justify-center rounded-xl bg-amber-500/10 text-amber-400">
              <ShieldAlert className="size-4" />
            </div>
          </div>
          <div className="mt-3">
            <span className="text-base font-semibold text-neutral-100 block truncate" title={stats?.top_failure_cause || "None"}>
              {stats?.top_failure_cause
                ? STAGE_LABELS[stats.top_failure_cause] || stats.top_failure_cause
                : "None"}
            </span>
          </div>
          <div className="mt-2 text-[11px] text-neutral-400">
            {stats?.failure_breakdown && stats.failure_breakdown.length > 0 ? (
              <span>
                {stats.failure_breakdown[0].count} events ({stats.failure_breakdown[0].percentage}%)
              </span>
            ) : (
              <span>Zero failures recorded</span>
            )}
          </div>
        </div>
      </div>

      {/* ── 2. Filter Bar ─────────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-4 shadow-sm backdrop-blur-sm">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Search Bar */}
          <div className="relative flex-1 min-w-[240px]">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 size-4 text-neutral-400" />
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="Search query text or user ERP ID..."
              className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light pl-10 pr-4 py-2 text-xs text-neutral-100 placeholder:text-neutral-500 outline-none transition-colors focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
            />
          </div>

          {/* Dropdown Filters */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Status Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-neutral-400">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => {
                  setStatusFilter(e.target.value)
                  setPage(1)
                }}
                className="rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1.5 text-xs text-neutral-200 outline-none focus:border-theme-red/50"
              >
                <option value="all">All Statuses</option>
                <option value="passed">Passed</option>
                <option value="failed">Failed</option>
                <option value="flagged">Flagged</option>
                <option value="fallback">Fallback</option>
              </select>
            </div>

            {/* Failure Stage Filter */}
            <div className="flex items-center gap-1.5">
              <span className="text-[11px] text-neutral-400">Stage:</span>
              <select
                value={stageFilter}
                onChange={(e) => {
                  setStageFilter(e.target.value)
                  setPage(1)
                }}
                className="rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1.5 text-xs text-neutral-200 outline-none focus:border-theme-red/50 max-w-[160px] truncate"
              >
                <option value="all">All Stages</option>
                <option value="safety_guardrail">Safety Guardrail</option>
                <option value="wellness_guardrail">Wellness Crisis</option>
                <option value="guest_gate">Guest Gate</option>
                <option value="access_denied">Access Control</option>
                <option value="academic_scope_missing">Academic Scope</option>
                <option value="retrieval_empty">Retrieval Empty</option>
                <option value="context_length_exceeded">Context Length</option>
                <option value="vllm_timeout">vLLM Timeout</option>
                <option value="generation_error">Generation Error</option>
              </select>
            </div>

            {/* Time Window */}
            <div className="flex items-center gap-1.5">
              <Clock className="size-3.5 text-neutral-400" />
              <select
                value={hours}
                onChange={(e) => {
                  setHours(Number(e.target.value))
                  setPage(1)
                }}
                className="rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1.5 text-xs text-neutral-200 outline-none focus:border-theme-red/50"
              >
                <option value={1}>Last 1 Hour</option>
                <option value={12}>Last 12 Hours</option>
                <option value={24}>Last 24 Hours</option>
                <option value={168}>Last 7 Days</option>
                <option value={720}>Last 30 Days</option>
              </select>
            </div>

            {/* Refresh Button */}
            <button
              onClick={() => {
                fetchStats()
                fetchTraces()
              }}
              disabled={loading || statsLoading}
              title="Refresh telemetry"
              className="flex items-center gap-1.5 rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1.5 text-xs font-medium text-neutral-300 hover:bg-theme-gray hover:text-white transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`size-3.5 ${loading || statsLoading ? "animate-spin text-theme-yellow" : ""}`} />
              <span>Refresh</span>
            </button>
          </div>
        </div>
      </div>

      {/* ── 3. Query Trace Table ─────────────────────────────────────────── */}
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 overflow-hidden shadow-sm backdrop-blur-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-theme-gray-light bg-theme-gray-light/40 text-neutral-400">
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">Time</th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">User / Role</th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">Query</th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">Status</th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">Failure Stage</th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">Sources</th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px]">Latency</th>
                <th className="py-3 px-4 font-semibold uppercase tracking-wider text-[10px] text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-theme-gray-light/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-neutral-400">
                    <RefreshCw className="size-5 animate-spin mx-auto mb-2 text-theme-yellow" />
                    <span>Loading query traces...</span>
                  </td>
                </tr>
              ) : items.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-16 text-center text-neutral-400">
                    <Info className="size-5 mx-auto mb-2 text-neutral-500" />
                    <p className="font-medium text-neutral-300">No query traces found</p>
                    <p className="text-[11px] text-neutral-500 mt-0.5">Try adjusting the filter criteria or time window.</p>
                  </td>
                </tr>
              ) : (
                items.map((item) => {
                  const statusUpper = (item.status || "").toLowerCase()
                  return (
                    <tr
                      key={item.id}
                      className="hover:bg-theme-gray-light/30 transition-colors cursor-pointer group"
                      onClick={() => setSelectedTrace(item)}
                    >
                      {/* Timestamp */}
                      <td className="py-3 px-4 text-neutral-400 whitespace-nowrap font-mono text-[11px]">
                        {formatDate(item.created_at)}
                      </td>

                      {/* User / Role */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-wider ${
                              item.user_role === "student"
                                ? "bg-blue-500/10 text-blue-400 border border-blue-500/20"
                                : item.user_role === "faculty"
                                ? "bg-purple-500/10 text-purple-400 border border-purple-500/20"
                                : item.user_role === "admin"
                                ? "bg-theme-red/10 text-theme-red border border-theme-red/20"
                                : "bg-neutral-500/10 text-neutral-400 border border-neutral-500/20"
                            }`}
                          >
                            {item.user_role || "Guest"}
                          </span>
                          {item.erp_id && (
                            <span className="text-[11px] font-mono text-neutral-300">
                              {item.erp_id}
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Query Text */}
                      <td className="py-3 px-4 max-w-xs md:max-w-md">
                        <p className="text-neutral-200 truncate font-medium group-hover:text-white" title={item.query_text}>
                          {item.query_text}
                        </p>
                        {item.is_personal_data && (
                          <span className="inline-block mt-0.5 text-[9px] font-semibold text-purple-400 bg-purple-500/10 px-1.5 py-0.2 rounded border border-purple-500/20">
                            Personal Scope
                          </span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        {statusUpper === "passed" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            <CheckCircle2 className="size-3" />
                            Passed
                          </span>
                        )}
                        {statusUpper === "failed" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
                            <XCircle className="size-3" />
                            Failed
                          </span>
                        )}
                        {statusUpper === "flagged" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            <ShieldAlert className="size-3" />
                            Flagged
                          </span>
                        )}
                        {statusUpper === "fallback" && (
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-neutral-500/10 text-neutral-400 border border-neutral-500/20">
                            <HelpCircle className="size-3" />
                            Fallback
                          </span>
                        )}
                      </td>

                      {/* Failure Stage */}
                      <td className="py-3 px-4 whitespace-nowrap">
                        {item.failure_stage && item.failure_stage !== "none" ? (
                          <div className="flex flex-col">
                            <span className="text-[11px] font-medium text-red-400">
                              {STAGE_LABELS[item.failure_stage] || item.failure_stage}
                            </span>
                            {item.failure_reason && (
                              <span className="text-[10px] text-neutral-500 truncate max-w-[140px]" title={item.failure_reason}>
                                {item.failure_reason}
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-[11px] text-neutral-500">—</span>
                        )}
                      </td>

                      {/* Sources */}
                      <td className="py-3 px-4 whitespace-nowrap font-mono text-[11px]">
                        {item.sources_count > 0 ? (
                          <span className="inline-flex items-center gap-1 text-neutral-300">
                            <FileText className="size-3 text-theme-yellow" />
                            {item.sources_count} {item.sources_count === 1 ? "source" : "sources"}
                          </span>
                        ) : (
                          <span className="text-neutral-500">0 sources</span>
                        )}
                      </td>

                      {/* Latency */}
                      <td className="py-3 px-4 whitespace-nowrap font-mono text-[11px]">
                        {item.latency_total_ms != null ? (
                          <span
                            className={
                              item.latency_total_ms > 3000
                                ? "text-amber-400"
                                : item.latency_total_ms > 6000
                                ? "text-red-400"
                                : "text-neutral-300"
                            }
                          >
                            {item.latency_total_ms}ms
                          </span>
                        ) : (
                          <span className="text-neutral-500">—</span>
                        )}
                      </td>

                      {/* Action */}
                      <td className="py-3 px-4 text-right whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedTrace(item)
                          }}
                          className="px-2.5 py-1 rounded-lg bg-theme-gray-light border border-theme-gray-lighter text-[11px] font-medium text-neutral-200 hover:text-white hover:bg-theme-gray transition-colors"
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* ── Pagination Controls ────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-theme-gray-light px-4 py-3 bg-theme-gray-light/20">
          <div className="text-[11px] text-neutral-400 font-sans">
            Showing{" "}
            <span className="font-semibold text-neutral-200">
              {totalItems === 0 ? 0 : (page - 1) * pageSize + 1}
            </span>{" "}
            to{" "}
            <span className="font-semibold text-neutral-200">
              {Math.min(page * pageSize, totalItems)}
            </span>{" "}
            of <span className="font-semibold text-neutral-200">{totalItems}</span> traces
          </div>

          <div className="flex items-center gap-2">
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(1)
              }}
              className="rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2 py-1 text-xs text-neutral-300 outline-none"
            >
              <option value={10}>10 / page</option>
              <option value={20}>20 / page</option>
              <option value={50}>50 / page</option>
              <option value={100}>100 / page</option>
            </select>

            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
              className="flex items-center gap-1 rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1 text-xs text-neutral-300 hover:bg-theme-gray disabled:opacity-40 transition-opacity"
            >
              <ChevronLeft className="size-3.5" />
              <span>Prev</span>
            </button>

            <span className="text-xs text-neutral-400 px-2 font-mono">
              {page} / {totalPages}
            </span>

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || loading}
              className="flex items-center gap-1 rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1 text-xs text-neutral-300 hover:bg-theme-gray disabled:opacity-40 transition-opacity"
            >
              <span>Next</span>
              <ChevronRight className="size-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* ── 4. Slide-out Inspection Drawer ─────────────────────────────────── */}
      {selectedTrace && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/70 backdrop-blur-sm animate-in fade-in duration-150">
          {/* Backdrop click dismiss */}
          <div className="flex-1" onClick={() => setSelectedTrace(null)} />

          {/* Drawer container */}
          <div className="w-full md:max-w-2xl bg-theme-black border-l border-theme-gray-light h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-200">
            {/* Header */}
            <div className="flex items-center justify-between p-5 border-b border-theme-gray-light bg-theme-gray/80">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-base font-bold text-neutral-100 font-sans">Query Trace Details</h2>
                  <span className="text-[10px] font-mono text-neutral-400 bg-theme-gray-light px-2 py-0.5 rounded border border-theme-gray-lighter">
                    {selectedTrace.id.slice(0, 8)}
                  </span>
                </div>
                <p className="text-xs text-neutral-400 mt-0.5 font-mono">
                  {formatDate(selectedTrace.created_at)}
                </p>
              </div>
              <button
                onClick={() => setSelectedTrace(null)}
                className="p-1.5 rounded-lg text-neutral-400 hover:text-white hover:bg-theme-gray-light transition-colors"
              >
                <X className="size-5" />
              </button>
            </div>

            {/* Scrollable Body */}
            <div className="flex-1 overflow-y-auto p-5 space-y-6">
              {/* Outcome Banner */}
              <div
                className={`p-4 rounded-xl border flex flex-col gap-2 ${
                  selectedTrace.status === "passed"
                    ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-300"
                    : selectedTrace.status === "flagged"
                    ? "bg-amber-500/10 border-amber-500/20 text-amber-300"
                    : "bg-red-500/10 border-red-500/20 text-red-300"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {selectedTrace.status === "passed" ? (
                      <CheckCircle2 className="size-4 text-emerald-400" />
                    ) : selectedTrace.status === "flagged" ? (
                      <ShieldAlert className="size-4 text-amber-400" />
                    ) : (
                      <XCircle className="size-4 text-red-400" />
                    )}
                    <span className="text-xs font-bold uppercase tracking-wider">
                      Execution {selectedTrace.status}
                    </span>
                  </div>
                  {selectedTrace.is_personal_data && (
                    <span className="text-[10px] uppercase tracking-wider font-semibold bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded border border-purple-500/30">
                      Personal Data
                    </span>
                  )}
                </div>

                {selectedTrace.failure_stage && selectedTrace.failure_stage !== "none" && (
                  <div className="mt-1 text-xs">
                    <p className="font-semibold text-neutral-200">
                      Failure Stage:{" "}
                      <span className="text-theme-yellow">
                        {STAGE_LABELS[selectedTrace.failure_stage] || selectedTrace.failure_stage}
                      </span>
                    </p>
                    {selectedTrace.failure_reason && (
                      <p className="text-[11px] text-neutral-300 mt-1 font-mono bg-black/40 p-2 rounded border border-white/5">
                        {selectedTrace.failure_reason}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Query & User Details */}
              <div className="rounded-xl border border-theme-gray-light bg-theme-gray/60 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 font-sans">
                    User Query
                  </span>
                  <button
                    onClick={() => handleCopyQuery(selectedTrace.query_text)}
                    className="flex items-center gap-1 text-[11px] text-neutral-400 hover:text-white transition-colors"
                  >
                    {copiedQuery ? <Check className="size-3 text-emerald-400" /> : <Copy className="size-3" />}
                    <span>{copiedQuery ? "Copied" : "Copy"}</span>
                  </button>
                </div>
                <p className="text-sm font-medium text-neutral-100 bg-theme-gray-light/60 p-3 rounded-lg border border-theme-gray-lighter">
                  {selectedTrace.query_text}
                </p>

                {/* Identity Metadata Pills */}
                <div className="flex flex-wrap gap-2 pt-1 text-[11px]">
                  <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-theme-gray-light border border-theme-gray-lighter text-neutral-300">
                    <User className="size-3 text-neutral-400" />
                    <span>Role: <strong className="text-neutral-100 capitalize">{selectedTrace.user_role || "guest"}</strong></span>
                  </div>
                  {selectedTrace.erp_id && (
                    <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-theme-gray-light border border-theme-gray-lighter text-neutral-300 font-mono">
                      <span>ERP: <strong className="text-neutral-100">{selectedTrace.erp_id}</strong></span>
                    </div>
                  )}
                  {selectedTrace.user_dept && (
                    <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-theme-gray-light border border-theme-gray-lighter text-neutral-300">
                      <span>Dept: <strong className="text-neutral-100">{selectedTrace.user_dept}</strong></span>
                    </div>
                  )}
                  {selectedTrace.query_type && (
                    <div className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-theme-gray-light border border-theme-gray-lighter text-neutral-300 font-mono">
                      <span>Type: <strong className="text-neutral-100">{selectedTrace.query_type}</strong></span>
                    </div>
                  )}
                </div>
              </div>

              {/* Latency Timing Waterfall */}
              <div className="rounded-xl border border-theme-gray-light bg-theme-gray/60 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Zap className="size-4 text-theme-yellow" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-neutral-300">
                      Timing Waterfall
                    </span>
                  </div>
                  <span className="text-xs font-mono font-bold text-neutral-100">
                    Total: {selectedTrace.latency_total_ms ?? 0}ms
                  </span>
                </div>

                {/* Waterfall Visual Bar */}
                {selectedTrace.latency_total_ms && selectedTrace.latency_total_ms > 0 ? (
                  <div className="space-y-2">
                    <div className="h-3 w-full rounded-full bg-theme-gray-light flex overflow-hidden">
                      {selectedTrace.latency_guardrail_ms != null && selectedTrace.latency_guardrail_ms > 0 && (
                        <div
                          style={{
                            width: `${Math.min(
                              100,
                              (selectedTrace.latency_guardrail_ms / selectedTrace.latency_total_ms) * 100
                            )}%`,
                          }}
                          className="bg-indigo-500 h-full"
                          title={`Guardrail: ${selectedTrace.latency_guardrail_ms}ms`}
                        />
                      )}
                      {selectedTrace.latency_retrieval_ms != null && selectedTrace.latency_retrieval_ms > 0 && (
                        <div
                          style={{
                            width: `${Math.min(
                              100,
                              (selectedTrace.latency_retrieval_ms / selectedTrace.latency_total_ms) * 100
                            )}%`,
                          }}
                          className="bg-amber-500 h-full"
                          title={`Retrieval: ${selectedTrace.latency_retrieval_ms}ms`}
                        />
                      )}
                      {selectedTrace.latency_generation_ms != null && selectedTrace.latency_generation_ms > 0 && (
                        <div
                          style={{
                            width: `${Math.min(
                              100,
                              (selectedTrace.latency_generation_ms / selectedTrace.latency_total_ms) * 100
                            )}%`,
                          }}
                          className="bg-emerald-500 h-full"
                          title={`Generation: ${selectedTrace.latency_generation_ms}ms`}
                        />
                      )}
                    </div>

                    {/* Breakdown Numbers */}
                    <div className="grid grid-cols-3 gap-2 pt-1 text-[10px]">
                      <div className="p-2 rounded bg-theme-gray-light/40 border border-theme-gray-lighter/40">
                        <div className="flex items-center gap-1 text-indigo-400 font-medium">
                          <span className="size-2 rounded-full bg-indigo-500" />
                          Guardrail
                        </div>
                        <div className="text-xs font-mono font-bold text-neutral-200 mt-1">
                          {selectedTrace.latency_guardrail_ms ?? 0}ms
                        </div>
                      </div>

                      <div className="p-2 rounded bg-theme-gray-light/40 border border-theme-gray-lighter/40">
                        <div className="flex items-center gap-1 text-amber-400 font-medium">
                          <span className="size-2 rounded-full bg-amber-500" />
                          Retrieval
                        </div>
                        <div className="text-xs font-mono font-bold text-neutral-200 mt-1">
                          {selectedTrace.latency_retrieval_ms ?? 0}ms
                        </div>
                      </div>

                      <div className="p-2 rounded bg-theme-gray-light/40 border border-theme-gray-lighter/40">
                        <div className="flex items-center gap-1 text-emerald-400 font-medium">
                          <span className="size-2 rounded-full bg-emerald-500" />
                          Generation
                        </div>
                        <div className="text-xs font-mono font-bold text-neutral-200 mt-1">
                          {selectedTrace.latency_generation_ms ?? 0}ms
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-[11px] text-neutral-500">Latency timing was not captured for this trace.</p>
                )}
              </div>

              {/* Answer Preview */}
              <div className="rounded-xl border border-theme-gray-light bg-theme-gray/60 p-4 space-y-3">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-neutral-400 font-sans block">
                  Generated Answer / Response
                </span>
                {selectedTrace.answer_preview ? (
                  <div className="rounded-lg bg-theme-gray-light/40 p-4 border border-theme-gray-lighter/50 text-xs text-neutral-200 leading-relaxed max-h-64 overflow-y-auto">
                    <MarkdownContent content={selectedTrace.answer_preview} />
                  </div>
                ) : (
                  <p className="text-xs text-neutral-500 italic">No answer generated.</p>
                )}
              </div>

              {/* Retrieved Sources */}
              <div className="rounded-xl border border-theme-gray-light bg-theme-gray/60 p-4 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-1.5">
                    <Database className="size-4 text-theme-yellow" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-neutral-300">
                      Retrieved Knowledge Sources
                    </span>
                  </div>
                  <span className="text-xs font-mono text-neutral-400">
                    {selectedTrace.sources_count} found
                  </span>
                </div>

                {selectedTrace.sources_fetched && selectedTrace.sources_fetched.length > 0 ? (
                  <div className="space-y-2">
                    {selectedTrace.sources_fetched.map((src, i) => (
                      <div
                        key={i}
                        className="p-3 rounded-lg bg-theme-gray-light/40 border border-theme-gray-lighter text-xs space-y-1"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-semibold text-neutral-200 break-all">
                            {src.title || src.file || src.path || `Source #${i + 1}`}
                          </span>
                          {src.score != null && (
                            <span className="font-mono text-[10px] text-theme-yellow bg-theme-yellow/10 px-1.5 py-0.5 rounded border border-theme-yellow/20">
                              Score: {Number(src.score).toFixed(3)}
                            </span>
                          )}
                        </div>
                        {src.file && src.file !== src.title && (
                          <div className="text-[11px] font-mono text-neutral-400 truncate">
                            File: {src.file}
                          </div>
                        )}
                        {(src.start_line != null || src.end_line != null) && (
                          <div className="text-[10px] font-mono text-neutral-500">
                            Lines: {src.start_line ?? 1}–{src.end_line ?? "?"}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded-lg bg-theme-gray-light/20 border border-theme-gray-lighter/30 text-center text-xs text-neutral-500">
                    No knowledge sources retrieved for this turn.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
