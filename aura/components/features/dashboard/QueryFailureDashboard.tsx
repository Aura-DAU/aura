"use client"

import React, { useState, useEffect, useCallback } from "react"
import {
  AlertTriangle,
  ExternalLink,
  CheckCircle2,
  Search,
  RefreshCw,
  Loader2,
  AlertCircle,
  Activity,
  Layers,
  Code,
  Eye,
  X,
} from "lucide-react"
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
} from "recharts"
import { getErrorMessage, toastError, toastSuccess } from "@/lib/toast"

interface FailureSummary {
  total_failures: number
  total_queries: number
  failure_rate: number
  window_days: number
  by_stage: { stage: string; count: number }[]
  by_code: { error_code: string; count: number }[]
  daily_trend: { date: string; count: number }[]
}

interface FailureItem {
  id: number
  stage: string
  error_code: string
  error_message: string
  query: string
  thread_id: string | null
  erp_id: string
  role: string
  langsmith_run_id: string | null
  langsmith_url: string | null
  created_at: string
  resolved_at: string | null
  resolved_by: string | null
}

const STAGE_COLORS: Record<string, string> = {
  guardrail: "#f43f5e", // rose-500
  access_control: "#dc2626", // red-600
  retrieval: "#f59e0b", // amber-500
  tool_execution: "#eab308", // yellow-500
  llm_generation: "#a855f7", // purple-500
  context_budget: "#f97316", // orange-500
  database: "#3b82f6", // blue-500
  pipeline: "#ef4444", // red-500
}

function getStageBadgeClass(stage: string): string {
  switch (stage) {
    case "guardrail":
      return "bg-rose-500/10 text-rose-400 border-rose-500/20"
    case "access_control":
      return "bg-red-600/10 text-red-400 border-red-600/20"
    case "retrieval":
      return "bg-amber-500/10 text-amber-400 border-amber-500/20"
    case "tool_execution":
      return "bg-yellow-500/10 text-yellow-400 border-yellow-500/20"
    case "llm_generation":
      return "bg-purple-500/10 text-purple-400 border-purple-500/20"
    case "context_budget":
      return "bg-orange-500/10 text-orange-400 border-orange-500/20"
    case "database":
      return "bg-blue-500/10 text-blue-400 border-blue-500/20"
    default:
      return "bg-neutral-500/10 text-neutral-400 border-neutral-500/20"
  }
}

export function QueryFailureDashboard() {
  const [days, setDays] = useState(7)
  const [summary, setSummary] = useState<FailureSummary | null>(null)
  const [failures, setFailures] = useState<FailureItem[]>([])
  const [totalFailuresCount, setTotalFailuresCount] = useState(0)
  const [loadingSummary, setLoadingSummary] = useState(false)
  const [loadingList, setLoadingList] = useState(false)
  const [selectedFailure, setSelectedFailure] = useState<FailureItem | null>(null)

  // Filters
  const [selectedStage, setSelectedStage] = useState<string>("")
  const [selectedCode, setSelectedCode] = useState<string>("")
  const [resolvedFilter, setResolvedFilter] = useState<string>("all")
  const [searchQuery, setSearchQuery] = useState<string>("")
  const [resolvingId, setResolvingId] = useState<number | null>(null)

  const fetchSummary = useCallback(async () => {
    setLoadingSummary(true)
    try {
      const res = await fetch(`/api/admin/failures/summary?days=${days}`)
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.error || "Failed to load failure summary")
      }
      const data = await res.json()
      setSummary(data)
    } catch (err) {
      toastError(getErrorMessage(err, "Failed to load failure metrics"))
    } finally {
      setLoadingSummary(false)
    }
  }, [days])

  const fetchFailures = useCallback(async () => {
    setLoadingList(true)
    try {
      const params = new URLSearchParams()
      params.set("days", days.toString())
      params.set("limit", "50")
      if (selectedStage) params.set("stage", selectedStage)
      if (selectedCode) params.set("code", selectedCode)
      if (resolvedFilter === "unresolved") params.set("resolved", "false")
      if (resolvedFilter === "resolved") params.set("resolved", "true")
      if (searchQuery.trim()) params.set("search", searchQuery.trim())

      const res = await fetch(`/api/admin/failures?${params.toString()}`)
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.error || "Failed to load failures list")
      }
      const data = await res.json()
      setFailures(data.items || [])
      setTotalFailuresCount(data.total || 0)
    } catch (err) {
      toastError(getErrorMessage(err, "Failed to load failures list"))
    } finally {
      setLoadingList(false)
    }
  }, [days, selectedStage, selectedCode, resolvedFilter, searchQuery])

  useEffect(() => {
    fetchSummary()
  }, [fetchSummary])

  useEffect(() => {
    fetchFailures()
  }, [fetchFailures])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchFailures()
  }

  const handleResolve = async (id: number) => {
    setResolvingId(id)
    try {
      const res = await fetch(`/api/admin/failures/${id}/resolve`, {
        method: "POST",
      })
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.error || "Failed to resolve failure")
      }
      toastSuccess(`Failure #${id} marked as resolved.`)
      setFailures((prev) =>
        prev.map((f) =>
          f.id === id ? { ...f, resolved_at: new Date().toISOString() } : f
        )
      )
      if (selectedFailure?.id === id) {
        setSelectedFailure((prev) =>
          prev ? { ...prev, resolved_at: new Date().toISOString() } : null
        )
      }
    } catch (err) {
      toastError(getErrorMessage(err, "Failed to resolve failure"))
    } finally {
      setResolvingId(null)
    }
  }

  const openDetail = (item: FailureItem) => {
    setSelectedFailure(item)
  }

  const stageChartData = (summary?.by_stage || []).map((s) => ({
    name: s.stage,
    count: Number(s.count),
    color: STAGE_COLORS[s.stage] || "#94a3b8",
  }))

  return (
    <div className="space-y-6">
      {/* Header & Window Selector */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-neutral-100 flex items-center gap-2">
            <AlertTriangle className="size-5 text-theme-red" />
            Query Failure Analyser
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Identify which user queries fail, diagnose root causes, and trace execution in LangSmith.
          </p>
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto">
          <div className="flex items-center rounded-xl bg-theme-gray border border-theme-gray-light p-1">
            {[
              { label: "24 Hours", val: 1 },
              { label: "7 Days", val: 7 },
              { label: "30 Days", val: 30 },
            ].map(({ label, val }) => (
              <button
                key={val}
                onClick={() => setDays(val)}
                className={`rounded-lg px-3 py-1 text-xs font-medium transition-colors ${
                  days === val
                    ? "bg-theme-red text-white"
                    : "text-neutral-400 hover:text-neutral-200"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          <button
            onClick={() => {
              fetchSummary()
              fetchFailures()
            }}
            disabled={loadingSummary || loadingList}
            className="flex items-center justify-center size-8 rounded-xl border border-theme-gray-light bg-theme-gray text-neutral-400 hover:text-neutral-100 disabled:opacity-50 transition-colors"
            title="Refresh Data"
          >
            <RefreshCw
              className={`size-4 ${loadingSummary || loadingList ? "animate-spin" : ""}`}
            />
          </button>
        </div>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <div className="rounded-xl border border-theme-gray-light bg-theme-gray/80 p-4">
          <div className="flex items-center gap-1.5 text-xs text-neutral-400 mb-1">
            <AlertCircle className="size-4 text-theme-red" />
            Total Failures
          </div>
          <div className="text-2xl font-bold text-neutral-100">
            {loadingSummary ? (
              <Loader2 className="size-5 animate-spin" />
            ) : (
              summary?.total_failures ?? 0
            )}
          </div>
          <div className="mt-1 text-[10px] text-neutral-500">
            In the last {days} days
          </div>
        </div>

        <div className="rounded-xl border border-theme-gray-light bg-theme-gray/80 p-4">
          <div className="flex items-center gap-1.5 text-xs text-neutral-400 mb-1">
            <Activity className="size-4 text-theme-yellow" />
            Failure Rate
          </div>
          <div className="text-2xl font-bold text-neutral-100">
            {loadingSummary ? (
              <Loader2 className="size-5 animate-spin" />
            ) : (
              `${summary?.failure_rate ?? 0}%`
            )}
          </div>
          <div className="mt-1 text-[10px] text-neutral-500">
            Of {summary?.total_queries ?? 0} total queries
          </div>
        </div>

        <div className="rounded-xl border border-theme-gray-light bg-theme-gray/80 p-4">
          <div className="flex items-center gap-1.5 text-xs text-neutral-400 mb-1">
            <Layers className="size-4 text-purple-400" />
            Top Stage
          </div>
          <div className="text-lg font-bold text-neutral-100 truncate">
            {loadingSummary ? (
              <Loader2 className="size-5 animate-spin" />
            ) : (
              summary?.by_stage?.[0]?.stage || "None"
            )}
          </div>
          <div className="mt-1 text-[10px] text-neutral-500">
            {summary?.by_stage?.[0]?.count ? `${summary.by_stage[0].count} incidents` : "Zero failures"}
          </div>
        </div>

        <div className="rounded-xl border border-theme-gray-light bg-theme-gray/80 p-4">
          <div className="flex items-center gap-1.5 text-xs text-neutral-400 mb-1">
            <Code className="size-4 text-cyan-400" />
            Top Error Code
          </div>
          <div className="text-lg font-bold text-neutral-100 truncate">
            {loadingSummary ? (
              <Loader2 className="size-5 animate-spin" />
            ) : (
              summary?.by_code?.[0]?.error_code || "None"
            )}
          </div>
          <div className="mt-1 text-[10px] text-neutral-500">
            {summary?.by_code?.[0]?.count ? `${summary.by_code[0].count} occurrences` : "No error codes"}
          </div>
        </div>
      </div>

      {/* Stage Breakdown Visualizer */}
      {stageChartData.length > 0 && (
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
          <h3 className="text-sm font-semibold text-neutral-200 mb-4 flex items-center justify-between">
            <span>Failures by Architectural Stage</span>
            <span className="text-xs text-neutral-500 font-normal">
              Click stage to filter
            </span>
          </h3>

          <div className="h-44 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={stageChartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 70, bottom: 5 }}
              >
                <XAxis type="number" stroke="#525252" fontSize={11} allowDecimals={false} />
                <YAxis
                  dataKey="name"
                  type="category"
                  stroke="#a3a3a3"
                  fontSize={11}
                  tickLine={false}
                  width={90}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#171717",
                    borderColor: "#333",
                    borderRadius: "8px",
                    color: "#f5f5f5",
                    fontSize: "12px",
                  }}
                  cursor={{ fill: "rgba(255,255,255,0.05)" }}
                />
                <Bar
                  dataKey="count"
                  radius={[0, 4, 4, 0]}
                  onClick={(entry) => {
                    const stage = entry?.name || ""
                    setSelectedStage(stage === selectedStage ? "" : stage)
                  }}
                  cursor="pointer"
                >
                  {stageChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      opacity={selectedStage && selectedStage !== entry.name ? 0.3 : 0.9}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-4 space-y-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-col gap-3 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-neutral-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search query, error message, or ERP ID..."
              className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light pl-9 pr-4 py-2 text-xs text-neutral-100 placeholder:text-neutral-500 outline-none focus:border-theme-red/60 focus:ring-1 focus:ring-theme-red/20"
            />
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Stage filter */}
            <select
              value={selectedStage}
              onChange={(e) => setSelectedStage(e.target.value)}
              className="rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3 py-2 text-xs text-neutral-200 outline-none focus:border-theme-red/60"
            >
              <option value="">All Stages</option>
              <option value="guardrail">Guardrail</option>
              <option value="access_control">Access Control</option>
              <option value="retrieval">Retrieval</option>
              <option value="tool_execution">Tool Execution</option>
              <option value="llm_generation">LLM Generation</option>
              <option value="context_budget">Context Budget</option>
              <option value="database">Database</option>
              <option value="pipeline">Pipeline</option>
            </select>

            {/* Resolution filter */}
            <select
              value={resolvedFilter}
              onChange={(e) => setResolvedFilter(e.target.value)}
              className="rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3 py-2 text-xs text-neutral-200 outline-none focus:border-theme-red/60"
            >
              <option value="all">All Statuses</option>
              <option value="unresolved">Unresolved</option>
              <option value="resolved">Resolved</option>
            </select>

            <button
              type="submit"
              className="rounded-xl bg-theme-red px-4 py-2 text-xs font-semibold text-white hover:bg-theme-red/90 transition-colors"
            >
              Filter
            </button>

            {(selectedStage || selectedCode || resolvedFilter !== "all" || searchQuery) && (
              <button
                type="button"
                onClick={() => {
                  setSelectedStage("")
                  setSelectedCode("")
                  setResolvedFilter("all")
                  setSearchQuery("")
                }}
                className="rounded-xl border border-neutral-700 bg-transparent px-3 py-2 text-xs text-neutral-400 hover:text-neutral-200 transition-colors"
              >
                Reset
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Failures List Table */}
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 overflow-hidden">
        <div className="p-4 border-b border-theme-gray-light flex items-center justify-between">
          <div className="text-xs text-neutral-400">
            Showing <span className="font-semibold text-neutral-200">{failures.length}</span> of{" "}
            <span className="font-semibold text-neutral-200">{totalFailuresCount}</span> failure incidents
          </div>
        </div>

        {loadingList ? (
          <div className="flex flex-col items-center justify-center p-12 text-neutral-400">
            <Loader2 className="size-6 animate-spin mb-2" />
            <span className="text-xs">Loading failure logs...</span>
          </div>
        ) : failures.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 text-neutral-500 text-xs">
            <CheckCircle2 className="size-8 text-green-500/50 mb-2" />
            No failures match the selected criteria.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-theme-gray-light bg-theme-gray-light/30 text-neutral-400 uppercase tracking-wider text-[10px]">
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4">Stage</th>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Query</th>
                  <th className="py-3 px-4">Error Code</th>
                  <th className="py-3 px-4">Trace</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-theme-gray-light/60">
                {failures.map((item) => (
                  <tr
                    key={item.id}
                    className={`hover:bg-theme-gray-light/20 transition-colors ${
                      item.resolved_at ? "opacity-60" : ""
                    }`}
                  >
                    <td className="py-3 px-4 whitespace-nowrap text-neutral-400">
                      {new Date(item.created_at).toLocaleString([], {
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-medium border ${getStageBadgeClass(
                          item.stage
                        )}`}
                      >
                        {item.stage}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="font-mono text-neutral-200">{item.erp_id}</span>
                      <span className="ml-1.5 text-[10px] text-neutral-500 uppercase">
                        ({item.role})
                      </span>
                    </td>
                    <td className="py-3 px-4 max-w-xs truncate text-neutral-300" title={item.query}>
                      {item.query}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="font-mono text-neutral-300 text-[11px]">
                        {item.error_code}
                      </span>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      {item.langsmith_url ? (
                        <a
                          href={item.langsmith_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-400 hover:text-emerald-300 underline underline-offset-2"
                        >
                          Trace
                          <ExternalLink className="size-3" />
                        </a>
                      ) : (
                        <span className="text-neutral-600 text-[11px]">—</span>
                      )}
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap text-right space-x-2">
                      <button
                        onClick={() => openDetail(item)}
                        className="p-1 text-neutral-400 hover:text-neutral-200 transition-colors"
                        title="View Details"
                      >
                        <Eye className="size-4" />
                      </button>

                      {!item.resolved_at ? (
                        <button
                          onClick={() => handleResolve(item.id)}
                          disabled={resolvingId === item.id}
                          className="px-2 py-1 rounded bg-theme-gray-light hover:bg-green-600/20 hover:text-green-400 border border-theme-gray-lighter text-neutral-300 text-[10px] transition-colors"
                        >
                          {resolvingId === item.id ? (
                            <Loader2 className="size-3 animate-spin inline" />
                          ) : (
                            "Resolve"
                          )}
                        </button>
                      ) : (
                        <span className="text-green-400 text-[10px] font-medium">Resolved</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Modal / Drawer for single failure details */}
      {selectedFailure && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
          <div className="relative w-full max-w-2xl rounded-2xl border border-theme-gray-light bg-neutral-900 p-6 text-neutral-100 shadow-2xl">
            <button
              onClick={() => setSelectedFailure(null)}
              className="absolute top-4 right-4 text-neutral-400 hover:text-neutral-100"
            >
              <X className="size-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <span
                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStageBadgeClass(
                  selectedFailure.stage
                )}`}
              >
                {selectedFailure.stage}
              </span>
              <span className="font-mono text-sm text-neutral-400">
                #{selectedFailure.id} &bull; {selectedFailure.error_code}
              </span>
            </div>

            <div className="space-y-4 text-xs">
              <div>
                <label className="text-[10px] uppercase font-semibold text-neutral-500">
                  User Query
                </label>
                <div className="mt-1 rounded-xl bg-neutral-800 p-3 text-neutral-200 border border-neutral-700/60 font-sans">
                  {selectedFailure.query}
                </div>
              </div>

              <div>
                <label className="text-[10px] uppercase font-semibold text-neutral-500">
                  Error Message
                </label>
                <div className="mt-1 rounded-xl bg-red-950/20 border border-red-900/40 p-3 text-red-300 font-mono">
                  {selectedFailure.error_message}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] uppercase font-semibold text-neutral-500">
                    User ERP / Role
                  </label>
                  <p className="mt-0.5 text-neutral-300">
                    {selectedFailure.erp_id} ({selectedFailure.role})
                  </p>
                </div>
                <div>
                  <label className="text-[10px] uppercase font-semibold text-neutral-500">
                    Thread ID
                  </label>
                  <p className="mt-0.5 text-neutral-300 font-mono">
                    {selectedFailure.thread_id || "None"}
                  </p>
                </div>
              </div>

              {selectedFailure.langsmith_url && (
                <div>
                  <label className="text-[10px] uppercase font-semibold text-neutral-500">
                    LangSmith Trace
                  </label>
                  <div className="mt-1">
                    <a
                      href={selectedFailure.langsmith_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 text-emerald-400 hover:bg-emerald-500/20 font-medium transition-colors"
                    >
                      <span>Open Full Trace in LangSmith</span>
                      <ExternalLink className="size-3.5" />
                    </a>
                  </div>
                </div>
              )}

              <div className="pt-2 flex justify-end gap-2">
                {!selectedFailure.resolved_at && (
                  <button
                    onClick={() => handleResolve(selectedFailure.id)}
                    disabled={resolvingId === selectedFailure.id}
                    className="rounded-xl bg-green-600 px-4 py-2 font-semibold text-white hover:bg-green-500 transition-colors"
                  >
                    {resolvingId === selectedFailure.id ? "Resolving..." : "Mark as Resolved"}
                  </button>
                )}
                <button
                  onClick={() => setSelectedFailure(null)}
                  className="rounded-xl border border-neutral-700 bg-neutral-800 px-4 py-2 text-neutral-300 hover:bg-neutral-700 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
