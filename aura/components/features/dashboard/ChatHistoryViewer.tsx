"use client"

import React, { useState, useEffect, useCallback } from "react"
import {
  MessageSquare,
  Search,
  User,
  Bot,
  ExternalLink,
  ShieldAlert,
  FileText,
  Loader2,
  RefreshCw,
} from "lucide-react"
import { getErrorMessage, toastError } from "@/lib/toast"

interface ThreadSummary {
  thread_id: string
  erp_id: string
  role: string
  title: string | null
  turn_count: number
  created_at: string
  last_active_at: string
}

interface MessageItem {
  id: number
  thread_id: string
  role: string
  content: string
  sources: Array<Record<string, unknown>> | null
  is_personal_data: boolean
  langsmith_run_id: string | null
  langsmith_url: string | null
  created_at: string
}

interface ConversationDetail {
  thread: ThreadSummary
  messages: MessageItem[]
}

export function ChatHistoryViewer() {
  const [threads, setThreads] = useState<ThreadSummary[]>([])
  const [totalThreads, setTotalThreads] = useState(0)
  const [loadingThreads, setLoadingThreads] = useState(false)
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null)
  const [conversationDetail, setConversationDetail] = useState<ConversationDetail | null>(null)
  const [loadingMessages, setLoadingMessages] = useState(false)

  // Filters
  const [searchQuery, setSearchQuery] = useState("")
  const [roleFilter, setRoleFilter] = useState("")

  const fetchThreads = useCallback(async () => {
    setLoadingThreads(true)
    try {
      const params = new URLSearchParams()
      params.set("limit", "50")
      if (roleFilter) params.set("role", roleFilter)
      if (searchQuery.trim()) params.set("search", searchQuery.trim())

      const res = await fetch(`/api/admin/conversations?${params.toString()}`)
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.error || "Failed to load conversations")
      }
      const data = await res.json()
      setThreads(data.items || [])
      setTotalThreads(data.total || 0)

      // Auto-select first thread if none selected
      setSelectedThreadId((prev) =>
        !prev && data.items && data.items.length > 0 ? data.items[0].thread_id : prev
      )
    } catch (err) {
      toastError(getErrorMessage(err, "Failed to load conversations"))
    } finally {
      setLoadingThreads(false)
    }
  }, [roleFilter, searchQuery])

  const fetchThreadDetail = useCallback(async (threadId: string) => {
    setLoadingMessages(true)
    try {
      const res = await fetch(`/api/admin/conversations/${encodeURIComponent(threadId)}`)
      if (!res.ok) {
        const errData = await res.json()
        throw new Error(errData.error || "Failed to load conversation messages")
      }
      const data = await res.json()
      setConversationDetail(data)
    } catch (err) {
      toastError(getErrorMessage(err, "Failed to load thread detail"))
    } finally {
      setLoadingMessages(false)
    }
  }, [])

  useEffect(() => {
    fetchThreads()
  }, [fetchThreads])

  useEffect(() => {
    if (selectedThreadId) {
      fetchThreadDetail(selectedThreadId)
    }
  }, [selectedThreadId, fetchThreadDetail])

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    fetchThreads()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-neutral-100 flex items-center gap-2">
            <MessageSquare className="size-5 text-theme-yellow" />
            Conversation Explorer
          </h2>
          <p className="text-xs text-neutral-400 mt-0.5">
            Inspect conversation threads across student, faculty, and guest users.
          </p>
        </div>

        <button
          onClick={fetchThreads}
          disabled={loadingThreads}
          className="flex items-center gap-1.5 self-start sm:self-auto rounded-xl border border-theme-gray-light bg-theme-gray px-3 py-1.5 text-xs text-neutral-300 hover:text-neutral-100 transition-colors"
        >
          <RefreshCw className={`size-3.5 ${loadingThreads ? "animate-spin" : ""}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Main Split Layout */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 min-h-[600px]">
        {/* Left Column: Thread List */}
        <div className="md:col-span-5 flex flex-col rounded-2xl border border-theme-gray-light bg-theme-gray/80 overflow-hidden">
          {/* Filters */}
          <div className="p-3.5 border-b border-theme-gray-light space-y-2.5">
            <form onSubmit={handleSearchSubmit} className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 size-3.5 text-neutral-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search ERP ID, Title, or Thread ID..."
                className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light pl-8 pr-3 py-1.5 text-xs text-neutral-100 placeholder:text-neutral-500 outline-none focus:border-theme-yellow/60"
              />
            </form>

            <div className="flex items-center justify-between text-xs">
              <select
                value={roleFilter}
                onChange={(e) => setRoleFilter(e.target.value)}
                className="rounded-lg border border-theme-gray-lighter bg-theme-gray-light px-2.5 py-1 text-xs text-neutral-300 outline-none"
              >
                <option value="">All Roles</option>
                <option value="student">Students</option>
                <option value="faculty">Faculty</option>
                <option value="guest">Guests</option>
                <option value="admin">Admins</option>
              </select>

              <span className="text-[11px] text-neutral-500">
                {threads.length} of {totalThreads} loaded
              </span>
            </div>
          </div>

          {/* Threads List Items */}
          <div className="flex-1 overflow-y-auto divide-y divide-theme-gray-light/60 max-h-[640px]">
            {loadingThreads && threads.length === 0 ? (
              <div className="flex flex-col items-center justify-center p-12 text-neutral-400">
                <Loader2 className="size-5 animate-spin mb-2" />
                <span className="text-xs">Loading conversations...</span>
              </div>
            ) : threads.length === 0 ? (
              <div className="p-8 text-center text-xs text-neutral-500">
                No conversations found.
              </div>
            ) : (
              threads.map((t) => {
                const isSelected = t.thread_id === selectedThreadId
                return (
                  <button
                    key={t.thread_id}
                    onClick={() => setSelectedThreadId(t.thread_id)}
                    className={`w-full text-left p-3.5 transition-colors flex flex-col gap-1.5 ${
                      isSelected
                        ? "bg-theme-gray-light/50 border-l-2 border-theme-yellow"
                        : "hover:bg-theme-gray-light/20"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-1.5">
                        <span className="font-mono text-xs font-semibold text-neutral-200">
                          {t.erp_id}
                        </span>
                        <span className="rounded px-1.5 py-0.2 text-[9px] font-medium uppercase tracking-wider bg-neutral-800 text-neutral-400 border border-neutral-700">
                          {t.role}
                        </span>
                      </div>
                      <span className="text-[10px] text-neutral-500">
                        {t.turn_count} {t.turn_count === 1 ? "turn" : "turns"}
                      </span>
                    </div>

                    <p className="text-xs text-neutral-300 line-clamp-1">
                      {t.title || "Untitled Conversation"}
                    </p>

                    <div className="flex items-center justify-between text-[10px] text-neutral-500 font-mono">
                      <span className="truncate max-w-[140px]" title={t.thread_id}>
                        #{t.thread_id.slice(0, 10)}...
                      </span>
                      <span>
                        {new Date(t.last_active_at).toLocaleDateString([], {
                          month: "short",
                          day: "numeric",
                        })}
                      </span>
                    </div>
                  </button>
                )
              })
            )}
          </div>
        </div>

        {/* Right Column: Message Transcript Inspector */}
        <div className="md:col-span-7 flex flex-col rounded-2xl border border-theme-gray-light bg-theme-gray/80 overflow-hidden">
          {selectedThreadId && conversationDetail ? (
            <>
              {/* Thread Inspector Header */}
              <div className="p-4 border-b border-theme-gray-light flex items-center justify-between bg-theme-gray-light/20">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-neutral-100">
                      User {conversationDetail.thread.erp_id}
                    </span>
                    <span className="rounded px-2 py-0.5 text-[10px] uppercase font-medium bg-neutral-800 text-neutral-300 border border-neutral-700">
                      {conversationDetail.thread.role}
                    </span>
                  </div>
                  <div className="text-[10px] text-neutral-400 font-mono mt-0.5">
                    Thread ID: {conversationDetail.thread.thread_id}
                  </div>
                </div>

                <div className="text-right text-[10px] text-neutral-500">
                  <div>Started: {new Date(conversationDetail.thread.created_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</div>
                  <div>Active: {new Date(conversationDetail.thread.last_active_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</div>
                </div>
              </div>

              {/* Messages Scroll Area */}
              <div className="flex-1 p-4 overflow-y-auto space-y-4 max-h-[640px]">
                {loadingMessages ? (
                  <div className="flex flex-col items-center justify-center p-12 text-neutral-400">
                    <Loader2 className="size-6 animate-spin mb-2" />
                    <span className="text-xs">Loading message history...</span>
                  </div>
                ) : conversationDetail.messages.length === 0 ? (
                  <div className="text-center p-12 text-xs text-neutral-500">
                    No messages recorded in this conversation thread.
                  </div>
                ) : (
                  conversationDetail.messages.map((msg) => {
                    const isUser = msg.role === "user"
                    return (
                      <div
                        key={msg.id}
                        className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}
                      >
                        {!isUser && (
                          <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-theme-red/20 text-theme-red border border-theme-red/30 text-xs">
                            <Bot className="size-4" />
                          </div>
                        )}

                        <div
                          className={`max-w-[85%] rounded-2xl p-3.5 text-xs space-y-2 ${
                            isUser
                              ? "bg-theme-gray-light border border-theme-gray-lighter text-neutral-100"
                              : "bg-neutral-900 border border-theme-gray-light text-neutral-200"
                          }`}
                        >
                          <div className="flex items-center justify-between gap-3 text-[10px] text-neutral-400">
                            <span className="font-semibold uppercase tracking-wide">
                              {isUser ? "User" : "AURA Assistant"}
                            </span>
                            <span>
                              {new Date(msg.created_at).toLocaleTimeString([], {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>

                          <div className="whitespace-pre-wrap leading-relaxed font-sans">
                            {msg.content}
                          </div>

                          {/* Sources and LangSmith trace link */}
                          {!isUser && (
                            <div className="pt-2 border-t border-neutral-800/80 flex flex-wrap items-center justify-between gap-2">
                              <div className="flex flex-wrap items-center gap-1.5">
                                {msg.is_personal_data && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-amber-500/10 text-amber-400 border border-amber-500/20">
                                    <ShieldAlert className="size-3" />
                                    Personal Data
                                  </span>
                                )}

                                {Array.isArray(msg.sources) && msg.sources.length > 0 && (
                                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] bg-neutral-800 text-neutral-400 border border-neutral-700">
                                    <FileText className="size-3" />
                                    {msg.sources.length} {msg.sources.length === 1 ? "source" : "sources"}
                                  </span>
                                )}
                              </div>

                              {msg.langsmith_url && (
                                <a
                                  href={msg.langsmith_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center gap-1 text-[10px] font-medium text-emerald-400 hover:text-emerald-300 underline underline-offset-2"
                                >
                                  Trace
                                  <ExternalLink className="size-3" />
                                </a>
                              )}
                            </div>
                          )}
                        </div>

                        {isUser && (
                          <div className="flex size-7 shrink-0 items-center justify-center rounded-lg bg-neutral-800 text-neutral-300 border border-neutral-700 text-xs">
                            <User className="size-4" />
                          </div>
                        )}
                      </div>
                    )
                  })
                )}
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full p-12 text-neutral-500 text-xs">
              <MessageSquare className="size-10 mb-3 opacity-30 text-theme-yellow" />
              Select a conversation thread from the left panel to inspect its transcript.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
