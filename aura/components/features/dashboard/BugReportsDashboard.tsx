"use client"

import React, { useCallback, useEffect, useMemo, useState } from "react"
import {
  Bug,
  Loader2,
  AlertCircle,
  ImageIcon,
  X,
  RefreshCw,
  LayoutGrid,
  BarChart3,
  ChevronRight,
  ChevronLeft,
  Clock,
  User,
} from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  Cell,
  PieChart,
  Pie,
} from "recharts"
import { toastError, toastSuccess, getErrorMessage } from "@/lib/toast"

// ── Types ────────────────────────────────────────────────────────────────

type BugStatus = "open" | "in_progress" | "resolved"

interface BugReport {
  id: number
  erp_id: string
  role: string
  query_text: string
  has_screenshot: boolean
  category: string
  status: BugStatus
  created_at: string
  updated_at: string | null
  resolved_at: string | null
  resolved_by: string | null
}

interface CategoryStat {
  category: string
  open: number
  in_progress: number
  resolved: number
  total: number
}

interface BugStats {
  total: number
  by_status: { open: number; in_progress: number; resolved: number }
  by_category: CategoryStat[]
}

// Keep in sync with server/api/schemas.py BUG_CATEGORIES.
const CATEGORY_LABELS: Record<string, string> = {
  chat_ai: "AURA Chat / AI",
  timetable: "Timetable",
  calendar: "Calendar",
  login_auth: "Login / Auth",
  performance: "Performance",
  ui_ux: "UI / Design",
  other: "Other",
}

const STATUS_META: Record<
  BugStatus,
  { label: string; accent: string; dot: string; bg: string; chartColor: string }
> = {
  open: {
    label: "Open",
    accent: "border-theme-red/30",
    dot: "bg-theme-red",
    bg: "bg-theme-red/5",
    chartColor: "#e53e3e",
  },
  in_progress: {
    label: "In Progress",
    accent: "border-theme-yellow/30",
    dot: "bg-theme-yellow",
    bg: "bg-theme-yellow/5",
    chartColor: "#eab308",
  },
  resolved: {
    label: "Resolved",
    accent: "border-green-500/30",
    dot: "bg-green-500",
    bg: "bg-green-500/5",
    chartColor: "#22c55e",
  },
}

const STATUS_ORDER: BugStatus[] = ["open", "in_progress", "resolved"]

function timeAgo(iso: string): string {
  const then = new Date(iso).getTime()
  if (Number.isNaN(then)) return ""
  const diffMs = Date.now() - then
  const mins = Math.floor(diffMs / 60000)
  if (mins < 1) return "just now"
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

function categoryLabel(cat: string): string {
  return CATEGORY_LABELS[cat] ?? cat
}

// ── Screenshot lightbox ─────────────────────────────────────────────────

function ScreenshotModal({ reportId, onClose }: { reportId: number; onClose: () => void }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    document.addEventListener("keydown", onKey)
    return () => document.removeEventListener("keydown", onKey)
  }, [onClose])

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/80 p-4 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative max-h-[85vh] max-w-3xl overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="absolute right-3 top-3 rounded-full bg-black/60 p-1.5 text-neutral-300 hover:bg-theme-red/80 hover:text-white transition-colors"
        >
          <X className="size-4" />
        </button>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`/api/admin/bug-reports/${reportId}/screenshot`}
          alt={`Screenshot for bug report #${reportId}`}
          className="max-h-[85vh] w-full object-contain"
        />
      </div>
    </div>
  )
}

// ── Bug card ─────────────────────────────────────────────────────────────

function BugCard({
  report,
  onMove,
  onViewScreenshot,
  moving,
}: {
  report: BugReport
  onMove: (id: number, status: BugStatus) => void
  onViewScreenshot: (id: number) => void
  moving: boolean
}) {
  const [expanded, setExpanded] = useState(false)
  const currentIdx = STATUS_ORDER.indexOf(report.status)
  const prevStatus = currentIdx > 0 ? STATUS_ORDER[currentIdx - 1] : null
  const nextStatus = currentIdx < STATUS_ORDER.length - 1 ? STATUS_ORDER[currentIdx + 1] : null

  return (
    <div className="rounded-xl border border-theme-gray-light bg-theme-gray-light/30 p-3.5 flex flex-col gap-2.5">
      <div className="flex items-center justify-between gap-2">
        <span className="rounded-full border border-theme-gray-lighter bg-theme-black px-2 py-0.5 text-[10px] font-medium text-neutral-300">
          {categoryLabel(report.category)}
        </span>
        <span className="text-[10px] text-neutral-500 shrink-0 flex items-center gap-1">
          <Clock className="size-2.5" />
          {timeAgo(report.created_at)}
        </span>
      </div>

      <p
        className={`text-xs text-neutral-200 leading-relaxed whitespace-pre-wrap ${expanded ? "" : "line-clamp-4"}`}
      >
        {report.query_text}
      </p>
      {report.query_text.length > 160 && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="self-start text-[10px] text-theme-yellow hover:underline"
        >
          {expanded ? "Show less" : "Show more"}
        </button>
      )}

      {report.has_screenshot && (
        <button
          type="button"
          onClick={() => onViewScreenshot(report.id)}
          className="flex items-center gap-1.5 self-start rounded-lg border border-theme-gray-lighter bg-theme-black px-2.5 py-1.5 text-[10px] text-neutral-300 hover:border-theme-yellow/50 hover:text-theme-yellow transition-colors"
        >
          <ImageIcon className="size-3" />
          View screenshot
        </button>
      )}

      <div className="flex items-center gap-1.5 text-[10px] text-neutral-500 pt-1 border-t border-theme-gray-light/60 mt-0.5">
        <User className="size-2.5" />
        <span className="font-mono truncate">{report.erp_id}</span>
        <span className="text-neutral-600">·</span>
        <span className="capitalize">{report.role}</span>
      </div>

      {report.resolved_by && report.status === "resolved" && (
        <div className="text-[10px] text-green-400/80">
          Resolved by {report.resolved_by}
          {report.resolved_at ? ` · ${timeAgo(report.resolved_at)}` : ""}
        </div>
      )}

      <div className="flex items-center justify-between gap-2 pt-1">
        <button
          type="button"
          disabled={!prevStatus || moving}
          onClick={() => prevStatus && onMove(report.id, prevStatus)}
          className="flex items-center gap-1 rounded-lg px-2 py-1.5 text-[10px] text-neutral-400 hover:bg-theme-gray-light hover:text-neutral-100 disabled:opacity-30 disabled:hover:bg-transparent transition-colors"
        >
          <ChevronLeft className="size-3" />
          {prevStatus ? STATUS_META[prevStatus].label : ""}
        </button>
        <button
          type="button"
          disabled={!nextStatus || moving}
          onClick={() => nextStatus && onMove(report.id, nextStatus)}
          className="flex items-center gap-1 rounded-lg bg-theme-gray-light px-2.5 py-1.5 text-[10px] font-medium text-neutral-200 hover:bg-theme-gray-lighter disabled:opacity-30 transition-colors"
        >
          {moving ? (
            <Loader2 className="size-3 animate-spin" />
          ) : (
            <>
              {nextStatus ? STATUS_META[nextStatus].label : "Done"}
              <ChevronRight className="size-3" />
            </>
          )}
        </button>
      </div>
    </div>
  )
}

// ── Board view ───────────────────────────────────────────────────────────

function BoardView({
  reports,
  loading,
  movingId,
  onMove,
  onViewScreenshot,
  categoryFilter,
  onCategoryFilterChange,
}: {
  reports: BugReport[]
  loading: boolean
  movingId: number | null
  onMove: (id: number, status: BugStatus) => void
  onViewScreenshot: (id: number) => void
  categoryFilter: string
  onCategoryFilterChange: (v: string) => void
}) {
  const columns = useMemo(() => {
    const grouped: Record<BugStatus, BugReport[]> = { open: [], in_progress: [], resolved: [] }
    for (const r of reports) grouped[r.status].push(r)
    return grouped
  }, [reports])

  return (
    <>
      <div className="mb-5 flex flex-wrap items-center gap-2">
        <label className="text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
          Category
        </label>
        <select
          value={categoryFilter}
          onChange={(e) => onCategoryFilterChange(e.target.value)}
          className="rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1.5 text-xs text-neutral-200 outline-none focus:border-theme-red/50"
        >
          <option value="">All categories</option>
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-20 text-neutral-500">
          <Loader2 className="size-6 animate-spin" />
        </div>
      ) : reports.length === 0 ? (
        <div className="text-center py-16 rounded-xl bg-theme-gray-light/20 border border-theme-gray-light">
          <Bug className="size-6 mx-auto mb-2 text-neutral-600" />
          <p className="text-xs text-neutral-500">No bug reports found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {STATUS_ORDER.map((status) => {
            const meta = STATUS_META[status]
            const items = columns[status]
            return (
              <div
                key={status}
                className={`rounded-2xl border ${meta.accent} ${meta.bg} p-3.5 flex flex-col gap-3 min-h-[200px]`}
              >
                <div className="flex items-center justify-between px-1">
                  <div className="flex items-center gap-2">
                    <span className={`size-2 rounded-full ${meta.dot}`} />
                    <h3 className="text-xs font-semibold text-neutral-200">{meta.label}</h3>
                  </div>
                  <span className="rounded-full bg-theme-black/60 px-2 py-0.5 text-[10px] font-mono text-neutral-400">
                    {items.length}
                  </span>
                </div>
                <div className="flex flex-col gap-3 max-h-[70vh] overflow-y-auto pr-0.5">
                  {items.length === 0 ? (
                    <p className="text-[10px] text-neutral-600 px-1">Nothing here.</p>
                  ) : (
                    items.map((r) => (
                      <BugCard
                        key={r.id}
                        report={r}
                        onMove={onMove}
                        onViewScreenshot={onViewScreenshot}
                        moving={movingId === r.id}
                      />
                    ))
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}
    </>
  )
}

// ── Statistics view ──────────────────────────────────────────────────────

function StatsView({ stats, loading }: { stats: BugStats | null; loading: boolean }) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20 text-neutral-500">
        <Loader2 className="size-6 animate-spin" />
      </div>
    )
  }

  if (!stats || stats.total === 0) {
    return (
      <div className="text-center py-16 rounded-xl bg-theme-gray-light/20 border border-theme-gray-light">
        <BarChart3 className="size-6 mx-auto mb-2 text-neutral-600" />
        <p className="text-xs text-neutral-500">No bug report data yet.</p>
      </div>
    )
  }

  const pieData = STATUS_ORDER.map((s) => ({
    name: STATUS_META[s].label,
    value: stats.by_status[s],
    color: STATUS_META[s].chartColor,
  })).filter((d) => d.value > 0)

  const barData = stats.by_category.map((c) => ({
    category: categoryLabel(c.category),
    Open: c.open,
    "In Progress": c.in_progress,
    Resolved: c.resolved,
  }))

  const topCategory = stats.by_category[0]

  return (
    <div className="space-y-6">
      {/* Summary cards */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-xl bg-theme-gray-light/30 border border-theme-gray-light/50 p-4">
          <div className="text-xs text-neutral-400 mb-1">Total Reports</div>
          <div className="text-2xl font-bold text-neutral-100">{stats.total}</div>
        </div>
        {STATUS_ORDER.map((s) => (
          <div
            key={s}
            className={`rounded-xl border p-4 ${STATUS_META[s].accent} ${STATUS_META[s].bg}`}
          >
            <div className="flex items-center gap-1.5 text-xs text-neutral-400 mb-1">
              <span className={`size-1.5 rounded-full ${STATUS_META[s].dot}`} />
              {STATUS_META[s].label}
            </div>
            <div className="text-2xl font-bold text-neutral-100">{stats.by_status[s]}</div>
          </div>
        ))}
      </div>

      {topCategory && (
        <div className="rounded-xl border border-theme-yellow/20 bg-theme-yellow/5 p-4 text-xs text-neutral-300">
          <span className="font-semibold text-theme-yellow">{categoryLabel(topCategory.category)}</span>{" "}
          has the most bug reports overall ({topCategory.total} total — {topCategory.open} still open).
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Category breakdown */}
        <div className="lg:col-span-3 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
          <h3 className="text-sm font-semibold text-neutral-200 mb-4">Bugs by Category</h3>
          <div className="h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={barData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                <XAxis
                  dataKey="category"
                  stroke="#666"
                  tick={{ fill: "#888", fontSize: 10 }}
                  interval={0}
                  angle={-25}
                  textAnchor="end"
                  height={60}
                />
                <YAxis stroke="#666" tick={{ fill: "#888", fontSize: 11 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "#0a0a0a",
                    border: "1px solid #333",
                    borderRadius: 8,
                    fontSize: 11,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="Open" stackId="a" fill={STATUS_META.open.chartColor} />
                <Bar dataKey="In Progress" stackId="a" fill={STATUS_META.in_progress.chartColor} />
                <Bar dataKey="Resolved" stackId="a" fill={STATUS_META.resolved.chartColor} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Status split */}
        <div className="lg:col-span-2 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
          <h3 className="text-sm font-semibold text-neutral-200 mb-4">Status Split</h3>
          <div className="h-[320px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={pieData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={55}
                  outerRadius={90}
                  paddingAngle={2}
                >
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "#0a0a0a",
                    border: "1px solid #333",
                    borderRadius: 8,
                    fontSize: 11,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Category table */}
      <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
        <h3 className="text-sm font-semibold text-neutral-200 mb-4">Category Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-left text-neutral-500 border-b border-theme-gray-light">
                <th className="pb-2 font-medium">Category</th>
                <th className="pb-2 font-medium text-right">Open</th>
                <th className="pb-2 font-medium text-right">In Progress</th>
                <th className="pb-2 font-medium text-right">Resolved</th>
                <th className="pb-2 font-medium text-right">Total</th>
              </tr>
            </thead>
            <tbody>
              {stats.by_category.map((c) => (
                <tr key={c.category} className="border-b border-theme-gray-light/40 last:border-0">
                  <td className="py-2 text-neutral-200">{categoryLabel(c.category)}</td>
                  <td className="py-2 text-right text-theme-red">{c.open}</td>
                  <td className="py-2 text-right text-theme-yellow">{c.in_progress}</td>
                  <td className="py-2 text-right text-green-400">{c.resolved}</td>
                  <td className="py-2 text-right font-semibold text-neutral-100">{c.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

// ── Root component ──────────────────────────────────────────────────────

export function BugReportsDashboard() {
  const [tab, setTab] = useState<"board" | "stats">("board")
  const [reports, setReports] = useState<BugReport[]>([])
  const [loadingReports, setLoadingReports] = useState(false)
  const [stats, setStats] = useState<BugStats | null>(null)
  const [loadingStats, setLoadingStats] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState("")
  const [movingId, setMovingId] = useState<number | null>(null)
  const [screenshotId, setScreenshotId] = useState<number | null>(null)

  const fetchReports = useCallback(async () => {
    setLoadingReports(true)
    setError(null)
    try {
      const qs = new URLSearchParams()
      if (categoryFilter) qs.set("category", categoryFilter)
      qs.set("limit", "200")
      const res = await fetch(`/api/admin/bug-reports?${qs.toString()}`, { cache: "no-store" })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "Failed to load bug reports")
      setReports(data.reports || [])
    } catch (err) {
      const msg = getErrorMessage(err, "Failed to load bug reports.")
      setError(msg)
      toastError(msg)
    } finally {
      setLoadingReports(false)
    }
  }, [categoryFilter])

  const fetchStats = useCallback(async () => {
    setLoadingStats(true)
    try {
      const res = await fetch(`/api/admin/bug-reports/stats`, { cache: "no-store" })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "Failed to load statistics")
      setStats(data)
    } catch (err) {
      toastError(getErrorMessage(err, "Failed to load bug statistics."))
    } finally {
      setLoadingStats(false)
    }
  }, [])

  useEffect(() => {
    fetchReports()
  }, [fetchReports])

  useEffect(() => {
    if (tab === "stats") fetchStats()
  }, [tab, fetchStats])

  const handleMove = async (id: number, status: BugStatus) => {
    setMovingId(id)
    // Optimistic update so the board feels instant.
    const prev = reports
    setReports((rs) => rs.map((r) => (r.id === id ? { ...r, status } : r)))
    try {
      const res = await fetch(`/api/admin/bug-reports/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || "Failed to update status")
      setReports((rs) => rs.map((r) => (r.id === id ? { ...r, ...data } : r)))
      toastSuccess(`Moved to ${STATUS_META[status].label}`)
      if (tab === "stats" || stats) fetchStats()
    } catch (err) {
      setReports(prev)
      toastError(getErrorMessage(err, "Failed to update bug report."))
    } finally {
      setMovingId(null)
    }
  }

  const refresh = () => {
    fetchReports()
    if (tab === "stats") fetchStats()
  }

  return (
    <div className="mt-8 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-lg bg-theme-red/10 border border-theme-red/20 text-theme-red">
            <Bug className="size-4" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-neutral-200">Bug Reports</h2>
            <p className="text-[10px] text-neutral-500">
              Triage and resolve bugs filed from the &quot;Report a Bug&quot; panel.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex rounded-lg border border-theme-gray-lighter bg-theme-black p-0.5">
            <button
              type="button"
              onClick={() => setTab("board")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === "board" ? "bg-theme-gray-light text-neutral-100" : "text-neutral-500 hover:text-neutral-300"
              }`}
            >
              <LayoutGrid className="size-3.5" />
              Board
            </button>
            <button
              type="button"
              onClick={() => setTab("stats")}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                tab === "stats" ? "bg-theme-gray-light text-neutral-100" : "text-neutral-500 hover:text-neutral-300"
              }`}
            >
              <BarChart3 className="size-3.5" />
              Statistics
            </button>
          </div>
          <button
            type="button"
            onClick={refresh}
            aria-label="Refresh"
            className="rounded-lg p-2 text-neutral-500 hover:bg-theme-gray-light hover:text-neutral-100 transition-colors"
          >
            <RefreshCw className={`size-3.5 ${loadingReports || loadingStats ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-xl border border-theme-red/20 bg-theme-red/5 p-3 text-xs text-theme-red">
          <AlertCircle className="size-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {tab === "board" ? (
        <BoardView
          reports={reports}
          loading={loadingReports}
          movingId={movingId}
          onMove={handleMove}
          onViewScreenshot={setScreenshotId}
          categoryFilter={categoryFilter}
          onCategoryFilterChange={setCategoryFilter}
        />
      ) : (
        <StatsView stats={stats} loading={loadingStats} />
      )}

      {screenshotId !== null && (
        <ScreenshotModal reportId={screenshotId} onClose={() => setScreenshotId(null)} />
      )}
    </div>
  )
}
