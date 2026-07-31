"use client"

import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import type {
  ChatMessage,
  ChatThread,
  Citation,
  StudentProfile,
  CalendarActionData,
} from "@/lib/chat-types"
import { useSession } from "next-auth/react"
import { apiFetch } from "@/lib/auth-client"
import { getUserMessage, toastAppError, toastError, toastSuccess, appErrorFromResponse } from "@/lib/toast"
import { AppError, isAbortError } from "@/lib/errors"

const STORAGE_KEY  = "aura-threads-v2"
const PROFILE_KEY  = "aura-profile-v2"

interface StoredThread extends ChatThread {
  messages: ChatMessage[]
}

const DEFAULT_PROFILE: StudentProfile = {
  name: "",
  program: "",
  year: "",
  interests: "",
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10)
}

function deriveTitle(text: string): string {
  const clean = text.trim().replace(/\s+/g, " ")
  return clean.length > 40 ? `${clean.slice(0, 40)}…` : clean || "New chat"
}

/** Last-activity timestamp for sidebar ordering / server merge. */
function threadUpdatedAt(messages: ChatMessage[], fallback = Date.now()): number {
  for (let i = messages.length - 1; i >= 0; i--) {
    const ts = messages[i]?.timestamp
    if (typeof ts === "number" && ts > 0) return ts
  }
  return fallback
}

function sortThreadsByRecency(threads: StoredThread[]): StoredThread[] {
  return [...threads].sort(
    (a, b) =>
      (b.updatedAt ?? threadUpdatedAt(b.messages, 0)) -
      (a.updatedAt ?? threadUpdatedAt(a.messages, 0)),
  )
}

function toBackendProfile(p: StudentProfile) {
  const out: Record<string, string> = {}
  if (p.name) out.name = p.name
  if (p.program) out.branch = p.program
  if (p.year) out.year = p.year
  if (p.interests) out.interests = p.interests
  return Object.keys(out).length ? out : undefined
}

// Maps messages to the backend turn shape. Callers pass an already-bounded
// tail (the unsummarised turns); the backend's ConversationMemory folds any
// overflow into the running summary, so no fixed slice is applied here.
function toBackendHistory(messages: ChatMessage[]) {
  return messages.map(({ role, content }) => ({ role, content }))
}

// Fire-and-forget — never blocks the UI. Coalesces concurrent saves so an
// older in-flight POST cannot overwrite a newer snapshot on the server.
let historySyncSeq = 0

function saveHistoryToServer(
  email: string,
  threads: (StoredThread & { messages: ChatMessage[] })[]
): void {
  const payload = threads.slice(0, 10)
  const seq = ++historySyncSeq
  apiFetch("/api/auth/history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      threads: payload,
      // Monotonic client watermark — server rejects older snapshots.
      clientSyncAt: Math.max(
        Date.now(),
        ...payload.map((t) => t.updatedAt ?? 0),
      ),
    }),
  })
    .then(async (res) => {
      if (!res.ok && seq === historySyncSeq) {
        /* ignore — next successful sync will catch up */
      }
    })
    .catch(() => { /* ignore network errors */ })
}

/**
 * Returns a copy of threads with personal-data assistant message content
 * replaced by a redaction placeholder. The live UI state is unaffected —
 * only the copy written to localStorage / the server is redacted.
 */
function redactPersonalDataMessages(threads: StoredThread[]): StoredThread[] {
  return threads.map((t) => ({
    ...t,
    messages: t.messages.map((m) =>
      m.is_personal_data
        ? { ...m, content: "[Personal data — not stored]" }
        : m
    ),
  }))
}

async function* parseSSEStream(response: Response, signal?: AbortSignal) {
  if (!response.body) throw new Error("No response body")
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (true) {
      if (signal?.aborted) {
        await reader.cancel().catch(() => {})
        return
      }
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n")
      buffer = lines.pop() || ""
      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith("data:")) {
          const data = trimmed.slice(5).trim()
          if (data === "[DONE]") return
          try {
            yield JSON.parse(data)
          } catch {
            /* skip malformed chunk */
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}

export function useAuraChat() {
  const [threads, setThreads] = useState<StoredThread[]>([])
  const [activeThreadId, setActiveThreadIdState] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState("")
  const [loading, setLoading] = useState(false)
  const [thinkingStep, setThinkingStep] = useState<string | undefined>(undefined)
  const [isRecording, setIsRecording] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [recordingVolume, setRecordingVolume] = useState(0)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [activeCitations, setActiveCitations] = useState<Citation[]>([])
  const [studentProfile, setStudentProfile] = useState<StudentProfile>(DEFAULT_PROFILE)
  const [remainingQuota, setRemainingQuotaState] = useState<number | null>(null)
  const [hasHydrated, setHasHydrated] = useState(false)
  const { data: session, status: sessionStatus } = useSession()

  // Guest quota policy: signed-in @dau.ac.in accounts (student/faculty/admin)
  // are unlimited — the backend never returns a limit for them, so we show
  // no counter. Anonymous guests (no session at all) get 10 questions/day;
  // the real enforcement lives server-side against a cookie-scoped
  // anonymous id, this is just a local mirror for the UI counter.
  const GUEST_DAILY_QUOTA = 10
  const GUEST_QUOTA_KEY = "aura-quota-guest"

  useEffect(() => {
    if (sessionStatus === "loading") return
    if (session?.user) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setRemainingQuotaState(null)
      return
    }

    const refreshGuestQuota = () => {
      const maxQuota = GUEST_DAILY_QUOTA
      const date = new Date().toISOString().split("T")[0]
      try {
        const stored = localStorage.getItem(GUEST_QUOTA_KEY)
        if (stored) {
          const parsed = JSON.parse(stored) as { date?: string; count?: number }
          if (parsed.date === date) {
            setRemainingQuotaState(Math.max(0, maxQuota - (parsed.count ?? 0)))
            return
          }
        }
        setRemainingQuotaState(maxQuota)
        localStorage.setItem(GUEST_QUOTA_KEY, JSON.stringify({ date, count: 0 }))
      } catch {
        setRemainingQuotaState(maxQuota)
      }
    }

    refreshGuestQuota()
    const onVisible = () => {
      if (document.visibilityState === "visible") refreshGuestQuota()
    }
    window.addEventListener("focus", refreshGuestQuota)
    document.addEventListener("visibilitychange", onVisible)
    return () => {
      window.removeEventListener("focus", refreshGuestQuota)
      document.removeEventListener("visibilitychange", onVisible)
    }
  }, [session, sessionStatus])

  // Authoritative sync from the server's response (see "quota" SSE event /
  // X-Quota-Remaining header). This is the source of truth — it replaces
  // whatever the client's own optimistic counter believed, so the two can
  // never silently drift apart (which previously could make the UI show
  // "quota reached" far earlier than 10 real questions if the server-side
  // count was already ahead of what the client had locally tracked).
  const syncQuotaFromServer = useCallback((remaining: number) => {
    setRemainingQuotaState(Math.max(0, remaining))
    if (!session?.user) {
      const maxQuota = GUEST_DAILY_QUOTA
      const date = new Date().toISOString().split('T')[0]
      try {
        localStorage.setItem(
          GUEST_QUOTA_KEY,
          JSON.stringify({ date, count: Math.max(0, maxQuota - remaining) }),
        )
      } catch { }
    }
  }, [session])

  // Optimistic local decrement — used only as an immediate UI response
  // before the server's authoritative count (syncQuotaFromServer) arrives
  // for this same request.
  const decrementQuota = useCallback(() => {
    setRemainingQuotaState(prev => {
      if (prev === null) return null;
      const newVal = Math.max(0, prev - 1)
      if (!session?.user) {
        const maxQuota = GUEST_DAILY_QUOTA
        const date = new Date().toISOString().split('T')[0]
        const key = GUEST_QUOTA_KEY
        try {
          localStorage.setItem(key, JSON.stringify({ date, count: maxQuota - newVal }))
        } catch {}
      }
      return newVal
    })
  }, [session])

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const audioContextRef = useRef<AudioContext | null>(null)
  const animationFrameRef = useRef<number | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  // Set when a turn hard-overflows: the fork target for the NEXT message, so the
  // just-finished answer stays on screen until the user actually continues.
  const pendingContinuationRef = useRef<{ fromId: string; toId: string } | null>(null)
  const lastVolumeUpdateRef = useRef(0)
  const mountedRef = useRef(true)
  const activeThreadIdRef = useRef<string | null>(null)

  useEffect(() => {
    activeThreadIdRef.current = activeThreadId
  }, [activeThreadId])

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
      abortRef.current?.abort()
    }
  }, [])

  useEffect(() => {
    try {
      const rawThreads = localStorage.getItem(STORAGE_KEY)
      if (rawThreads) {
        const parsed = (JSON.parse(rawThreads) as StoredThread[]).map((t) => ({
          ...t,
          updatedAt: t.updatedAt ?? threadUpdatedAt(t.messages, 0),
        }))
        const sorted = sortThreadsByRecency(parsed)
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setThreads(sorted)
        if (sorted[0]) {
          setActiveThreadIdState(sorted[0].id)
          setMessages(sorted[0].messages)
        }
      }
      const rawProfile = localStorage.getItem(PROFILE_KEY)
      if (rawProfile) setStudentProfile(JSON.parse(rawProfile) as StudentProfile)
    } catch {
      /* ignore corrupt storage */
    }
    setHasHydrated(true)
  }, [])

  useEffect(() => {
    // Fetch history from server to synchronize across devices
    if (session?.user?.email) {
      apiFetch("/api/auth/history")
        .then(res => res.json())
        .then(data => {
          if (data.threads && Array.isArray(data.threads)) {
            setThreads(prev => {
              const map = new Map<string, StoredThread>()
              const activity = (t: StoredThread) =>
                t.updatedAt ?? threadUpdatedAt(t.messages, 0)
              for (const t of data.threads as StoredThread[]) {
                map.set(t.id, {
                  ...t,
                  updatedAt: activity(t),
                })
              }
              for (const t of prev) {
                const existing = map.get(t.id)
                if (!existing || activity(t) >= activity(existing)) {
                  map.set(t.id, t)
                }
              }
              const merged = sortThreadsByRecency(Array.from(map.values()))

              const activeId = activeThreadIdRef.current
              if (!prev.length && merged[0]) {
                setActiveThreadIdState(merged[0].id)
                setMessages(merged[0].messages)
              } else if (activeId) {
                // Only replace the open transcript when the merge actually
                // chose a newer copy (avoids clobbering an in-progress stream).
                const active = merged.find((t) => t.id === activeId)
                const prevActive = prev.find((t) => t.id === activeId)
                if (
                  active &&
                  (!prevActive || activity(active) > activity(prevActive))
                ) {
                  setMessages(active.messages)
                }
              }

              return merged
            })
          }
        })
        .catch(() => {})
    }
  }, [session?.user?.email])

  useEffect(() => {
    if (!hasHydrated) return
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(redactPersonalDataMessages(threads)))
    } catch {
      /* quota or unavailable */
    }
  }, [threads, hasHydrated])

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((t) => t.stop())
        streamRef.current = null
      }
      if (animationFrameRef.current !== null) {
        cancelAnimationFrame(animationFrameRef.current)
        animationFrameRef.current = null
      }
      if (audioContextRef.current) {
        void audioContextRef.current.close().catch(() => {})
        audioContextRef.current = null
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
        mediaRecorderRef.current.stop()
      }
    }
  }, [])

  const persistMessages = useCallback(
    (threadId: string, next: ChatMessage[], title?: string) => {
      const updatedAt = threadUpdatedAt(next)
      setThreads((prev) =>
        sortThreadsByRecency(
          prev.map((t) =>
            t.id === threadId
              ? { ...t, messages: next, title: title ?? t.title, updatedAt }
              : t,
          ),
        ),
      )
    },
    [],
  )

  const syncThreadsToServer = useCallback(
    (next: StoredThread[]) => {
      const email = session?.user?.email
      if (!email) return
      saveHistoryToServer(email, redactPersonalDataMessages(next))
    },
    [session?.user?.email],
  )

  const setActiveThreadId = useCallback(
    (id: string) => {
      abortRef.current?.abort()
      abortRef.current = null
      setLoading(false)
      setThinkingStep(undefined)
      setActiveThreadIdState(id)
      const thread = threads.find((t) => t.id === id)
      setMessages(thread ? thread.messages : [])
      setActiveCitations([])
      setErrorMessage(null)
    },
    [threads],
  )

  const startNewChat = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setLoading(false)
    setThinkingStep(undefined)
    setActiveThreadIdState(null)
    setMessages([])
    setActiveCitations([])
    setErrorMessage(null)
    setInputText("")
  }, [])

  const deleteThread = useCallback(
    (id: string) => {
      setThreads((prev) => {
        const next = prev.filter((t) => t.id !== id)
        if (id === activeThreadId) {
          if (next[0]) {
            setActiveThreadIdState(next[0].id)
            setMessages(next[0].messages)
          } else {
            setActiveThreadIdState(null)
            setMessages([])
          }
        }
        // Persist the omission so a later history GET cannot revive the thread.
        syncThreadsToServer(next)
        return next
      })
    },
    [activeThreadId, syncThreadsToServer],
  )

  const saveProfile = useCallback(async (p: StudentProfile) => {
    setStudentProfile(p)
    try {
      localStorage.setItem(PROFILE_KEY, JSON.stringify(p))
    } catch {
      /* ignore */
    }
  }, [])

  const handleSendMessage = useCallback(
    async (text: string, options?: { regenerate?: boolean }) => {
      const trimmed = text.trim()
      if (!trimmed || loading || remainingQuota === 0) return

      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      setErrorMessage(null)
      if (!options?.regenerate) {
        setInputText("")
      }

      // If the previous turn hard-overflowed, continue in the fresh thread we
      // forked for it. Deferred to now (not at fork time) so the answer the user
      // just read stayed on screen; use locals, not state, to dodge stale
      // closures within this tick.
      const pending = pendingContinuationRef.current
      let threadId = activeThreadId
      let priorMessages = messages
      if (pending && activeThreadId === pending.fromId) {
        pendingContinuationRef.current = null
        threadId = pending.toId
        priorMessages = []
        setActiveThreadIdState(pending.toId)
        setActiveCitations([])
      }

      const userMsg: ChatMessage = {
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      }

      // Regenerate: transcript already ends at the last user turn — do not
      // append a duplicate user message. History sent to the backend must
      // exclude that current user turn (same as a normal send).
      let baseMessages: ChatMessage[]
      if (options?.regenerate) {
        if (!threadId) return
        const last = priorMessages[priorMessages.length - 1]
        if (last?.role === "user" && last.content.trim() === trimmed) {
          baseMessages = priorMessages
          priorMessages = priorMessages.slice(0, -1)
        } else {
          baseMessages = [...priorMessages, userMsg]
        }
      } else {
        if (!threadId) {
          threadId = uid()
          const newThread: StoredThread = {
            id: threadId,
            title: deriveTitle(trimmed),
            messages: [userMsg],
            updatedAt: userMsg.timestamp,
          }
          setThreads((prev) => sortThreadsByRecency([newThread, ...prev]))
          setActiveThreadIdState(threadId)
        }
        baseMessages = [...priorMessages, userMsg]
        persistMessages(
          threadId,
          baseMessages,
          deriveTitle(priorMessages[0]?.content ?? trimmed),
        )
      }

      setMessages(baseMessages)

      // Rolling memory: send the running summary + only the unsummarised tail,
      // bounded so the request stays under the 20-turn API cap. The backend
      // folds any overflow into the summary and streams the update back.
      const activeThread = threads.find((t) => t.id === threadId)
      const priorSummaryCount = activeThread?.summaryTurnCount ?? 0
      const threadSummary = activeThread?.summary
      const MAX_TAIL_TURNS = 16
      const tailStart = Math.max(priorSummaryCount, priorMessages.length - MAX_TAIL_TURNS)
      const tail = priorMessages.slice(tailStart)

      setLoading(true)
      setThinkingStep("Thinking…")

      try {
        const response = await apiFetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: trimmed,
            history: toBackendHistory(tail),
            summary: threadSummary,
            threadId,
            studentProfile: toBackendProfile(studentProfile),
          }),
          signal: controller.signal,
        })

        if (controller.signal.aborted || !mountedRef.current) return

        if (response.status === 429) {
          // Only pin the guest counter to 0. Signed-in users are unlimited;
          // a transient 429 must not permanently lock the composer.
          if (!session?.user) {
            setRemainingQuotaState(0)
          }
          throw AppError.rateLimited()
        }
        if (!response.ok || !response.body) {
          throw await appErrorFromResponse(response)
        }

        decrementQuota()

        let assistantText = ""
        let citations: Citation[] = []
        let isPersonalData = false
        let calendarAction: CalendarActionData | undefined
        let newSummary: string | undefined
        let foldedTurns = 0
        let continuationSummary: string | undefined
        const assistantMsg: ChatMessage = {
          role: "assistant",
          content: "",
          timestamp: Date.now(),
        }
        setMessages([...baseMessages, assistantMsg])

        for await (const chunk of parseSSEStream(response, controller.signal)) {
          if (controller.signal.aborted || !mountedRef.current) return
          if (chunk.type === "text-delta" && typeof chunk.delta === "string") {
            setThinkingStep(undefined)
            assistantText += chunk.delta
            setMessages((prev) => {
              const next = [...prev]
              next[next.length - 1] = { ...assistantMsg, content: assistantText }
              return next
            })
          } else if (chunk.type === "citations" && Array.isArray(chunk.citations)) {
            citations = chunk.citations as Citation[]
            setActiveCitations(citations)
          } else if (chunk.type === "personal-data-flag") {
            isPersonalData = true
          } else if (chunk.type === "summary-update" && typeof chunk.summary === "string") {
            // Backend compacted older turns into the running summary this turn.
            newSummary = chunk.summary
            foldedTurns = typeof chunk.foldedTurns === "number" ? chunk.foldedTurns : 0
          } else if (chunk.type === "thread-continuation" && typeof chunk.summary === "string") {
            // Hard overflow — the summary itself is full; continue in a new thread.
            continuationSummary = chunk.summary
          } else if (chunk.type === "quota" && typeof chunk.remaining === "number") {
            syncQuotaFromServer(chunk.remaining)
          } else if (
            chunk.type === "calendar-action" &&
            chunk.action !== null &&
            typeof chunk.action === "object"
          ) {
            // Backend M3 (Dhruvam) owns the calendar tool logic.
            // This handler activates when the backend emits a calendar-action event.
            calendarAction = chunk.action as CalendarActionData
          }
        }

        if (controller.signal.aborted || !mountedRef.current) return

        const finalMessages: ChatMessage[] = [
          ...baseMessages,
          {
            ...assistantMsg,
            content: assistantText,
            is_personal_data: isPersonalData || undefined,
            calendar_action: calendarAction,
          },
        ]
        setMessages(finalMessages)
        persistMessages(threadId, finalMessages)

        // Persist this turn's rolling-memory bookkeeping onto the thread so the
        // next request sends the updated digest and the advanced tail pointer.
        if (newSummary !== undefined) {
          const capturedSummary = newSummary
          const advancedCount = tailStart + foldedTurns
          setThreads((prev) =>
            sortThreadsByRecency(
              prev.map((t) =>
                t.id === threadId
                  ? {
                      ...t,
                      summary: capturedSummary,
                      summaryTurnCount: advancedCount,
                      updatedAt: t.updatedAt ?? threadUpdatedAt(t.messages),
                    }
                  : t,
              ),
            ),
          )
        }

        // Hard overflow: fork a fresh thread seeded with the summary and defer
        // the switch (pendingContinuationRef) so the just-read answer stays on
        // screen; the user's next message continues in the new thread.
        if (continuationSummary) {
          const contId = uid()
          const carriedSummary = newSummary ?? continuationSummary
          const contThread: StoredThread = {
            id: contId,
            title: `${activeThread?.title ?? deriveTitle(trimmed)} (cont.)`,
            messages: [],
            summary: carriedSummary,
            summaryTurnCount: 0,
            continuedFromId: threadId,
            updatedAt: Date.now(),
          }
          setThreads((prev) => sortThreadsByRecency([contThread, ...prev]))
          pendingContinuationRef.current = { fromId: threadId, toId: contId }
          toastSuccess(
            "This chat is getting long — I'll continue in a new thread and keep the summary.",
          )
        }

        if (session?.user?.email) {
          setThreads((current) => {
            syncThreadsToServer(current)
            return current
          })
        }
      } catch (err) {
        if (controller.signal.aborted || !mountedRef.current) return
        if (isAbortError(err)) return
        const msg = getUserMessage(err)
        setErrorMessage(msg)
        toastAppError(err)
        setMessages(baseMessages)
      } finally {
        if (abortRef.current === controller) abortRef.current = null
        if (mountedRef.current && !controller.signal.aborted) {
          setLoading(false)
          setThinkingStep(undefined)
        }
      }
    },
    [activeThreadId, loading, messages, threads, persistMessages, studentProfile, session, remainingQuota, decrementQuota, syncQuotaFromServer, syncThreadsToServer],
  )

  const handleClearChat = useCallback(() => {
    if (activeThreadId) {
      setThreads((prev) => {
        const next = sortThreadsByRecency(
          prev.map((t) =>
            t.id === activeThreadId
              ? {
                  ...t,
                  messages: [],
                  summary: undefined,
                  summaryTurnCount: undefined,
                  continuedFromId: undefined,
                  updatedAt: Date.now(),
                }
              : t,
          ),
        )
        syncThreadsToServer(next)
        return next
      })
    }
    setMessages([])
    setActiveCitations([])
    setErrorMessage(null)
    pendingContinuationRef.current = null
  }, [activeThreadId, syncThreadsToServer])

  /** Re-ask the last user turn without duplicating it in history. */
  const handleRegenerate = useCallback(() => {
    if (loading) return
    let lastUserIdx = -1
    for (let i = messages.length - 1; i >= 0; i--) {
      if (messages[i]?.role === "user") {
        lastUserIdx = i
        break
      }
    }
    if (lastUserIdx < 0) return
    const lastUser = messages[lastUserIdx]
    if (!lastUser?.content.trim()) return

    // Keep the last user turn; drop the assistant reply that followed it.
    const trimmedMessages = messages.slice(0, lastUserIdx + 1)
    setMessages(trimmedMessages)
    if (activeThreadId) {
      persistMessages(activeThreadId, trimmedMessages)
    }
    void handleSendMessage(lastUser.content, { regenerate: true })
  }, [loading, messages, activeThreadId, persistMessages, handleSendMessage])

  const stopGeneration = useCallback(() => {
    abortRef.current?.abort()
    abortRef.current = null
    setLoading(false)
    setThinkingStep(undefined)
  }, [])

  const lastUserMessage = messages.findLast((m) => m.role === "user")?.content ?? null

  // Stable identity unless threads actually change — consumers (Sidebar) can
  // skip re-renders instead of receiving a fresh array every hook render.
  const threadSummaries = useMemo(
    () =>
      threads.map(({ id, title, messages, updatedAt }) => ({
        id,
        title,
        updatedAt: updatedAt ?? threadUpdatedAt(messages, 0),
      })),
    [threads],
  )

  // True when the active thread was auto-forked on context overflow — drives the
  // "Continued from previous conversation" divider in MessageList.
  const activeThreadIsContinuation = useMemo(
    () => Boolean(threads.find((t) => t.id === activeThreadId)?.continuedFromId),
    [threads, activeThreadId],
  )

  const transcribeAudio = useCallback(
    async (blob: Blob) => {
      setIsTranscribing(true)
      try {
        const mimeType = blob.type
        let extension = "webm"
        if (mimeType) {
          const match = mimeType.match(/audio\/([^;]+)/)
          if (match && match[1]) {
            extension = match[1].toLowerCase()
          }
        }
        if (extension === "mpeg") extension = "mp3"
        if (extension.includes("aac")) extension = "aac"
        if (extension.includes("wav")) extension = "wav"
        if (extension.includes("mp4")) extension = "mp4"
        if (extension.includes("webm")) extension = "webm"
        if (extension.includes("ogg")) extension = "ogg"

        const form = new FormData()
        form.append("audio", blob, `recording.${extension}`)
        const res = await apiFetch("/api/speech", { method: "POST", body: form })
        if (!res.ok) {
          const err = await appErrorFromResponse(res)
          setErrorMessage(err.message)
          toastAppError(err)
          return
        }
        const data = (await res.json()) as { text?: string }
        const transcript = data.text
        if (transcript) {
          setInputText((prev) => (prev ? `${prev} ${transcript}` : transcript))
        } else {
          const msg = "Could not transcribe audio. Please try again."
          setErrorMessage(msg)
          toastError(msg)
        }
      } catch (err) {
        if (isAbortError(err)) return
        const msg = getUserMessage(err, "Could not transcribe audio. Please try again.")
        setErrorMessage(msg)
        toastAppError(err, msg)
      } finally {
        setIsTranscribing(false)
      }
    },
    [],
  )

  const handleMicClick = useCallback(async () => {
    if (isRecording) {
      mediaRecorderRef.current?.stop()
      setIsRecording(false)
      return
    }
    try {
      const mimeTypes = [
        "audio/webm",
        "audio/mp4",
        "audio/aac",
        "audio/ogg",
        "audio/wav",
      ]
      let detectedMimeType = ""
      if (typeof MediaRecorder !== "undefined") {
        for (const type of mimeTypes) {
          if (MediaRecorder.isTypeSupported(type)) {
            detectedMimeType = type
            break
          }
        }
      }

      if (!detectedMimeType) {
        const msg = "Audio recording is not supported in this browser."
        setErrorMessage(msg)
        toastError(msg)
        return
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      const recorder = new MediaRecorder(stream, { mimeType: detectedMimeType })
      audioChunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }

      // Initialize AudioContext for Silence Detection & Volume Visualizer
      type WindowWithWebkitAudio = Window & {
        webkitAudioContext?: typeof AudioContext
      }
      const AudioCtxClass =
        typeof window !== "undefined"
          ? window.AudioContext || (window as WindowWithWebkitAudio).webkitAudioContext
          : null
      if (AudioCtxClass) {
        try {
          const audioCtx = new AudioCtxClass()
          const source = audioCtx.createMediaStreamSource(stream)
          const analyser = audioCtx.createAnalyser()
          analyser.fftSize = 256
          source.connect(analyser)
          audioContextRef.current = audioCtx

          const bufferLength = analyser.frequencyBinCount
          const dataArray = new Uint8Array(bufferLength)

          let silentSince: number | null = null
          const SILENCE_THRESHOLD_DB = 10 // DB threshold for detecting silence
          const SILENCE_DURATION_MS = 1800 // Auto-stop after 1.8 seconds of silence

          const checkSilence = () => {
            if (!analyser) return
            analyser.getByteFrequencyData(dataArray)

            let sum = 0
            for (let i = 0; i < bufferLength; i++) {
              sum += dataArray[i]
            }
            const avgVol = sum / bufferLength

            const normalizedVol = Math.min(avgVol / 120, 1)
            const now = performance.now()
            if (now - lastVolumeUpdateRef.current >= 80) {
              lastVolumeUpdateRef.current = now
              setRecordingVolume(normalizedVol)
            }

            if (avgVol < SILENCE_THRESHOLD_DB) {
              if (silentSince === null) {
                silentSince = Date.now()
              } else if (Date.now() - silentSince > SILENCE_DURATION_MS) {
                // Silence threshold exceeded, auto-stop recording
                if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
                  mediaRecorderRef.current.stop()
                  setIsRecording(false)
                  return
                }
              }
            } else {
              silentSince = null
            }

            animationFrameRef.current = requestAnimationFrame(checkSilence)
          }

          animationFrameRef.current = requestAnimationFrame(checkSilence)
        } catch {
          /* Fallback gracefully if AudioContext initialization fails */
        }
      }

      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        streamRef.current = null
        if (animationFrameRef.current !== null) {
          cancelAnimationFrame(animationFrameRef.current)
          animationFrameRef.current = null
        }
        if (audioContextRef.current) {
          void audioContextRef.current.close().catch(() => {})
          audioContextRef.current = null
        }
        setRecordingVolume(0)

        const blob = new Blob(audioChunksRef.current, { type: detectedMimeType })
        void transcribeAudio(blob)
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setIsRecording(true)
    } catch {
      const msg = "Microphone access was denied."
      setErrorMessage(msg)
      toastError(msg)
    }
  }, [isRecording, transcribeAudio])

  return {
    messages,
    inputText,
    setInputText,
    loading,
    thinkingStep,
    isRecording,
    isTranscribing,
    recordingVolume,
    errorMessage,
    setErrorMessage,
    activeCitations,
    remainingQuota,
    threads: threadSummaries,
    activeThreadIsContinuation,
    activeThreadId,
    setActiveThreadId,
    startNewChat,
    deleteThread,
    studentProfile,
    saveProfile,
    handleMicClick,
    handleSendMessage,
    handleRegenerate,
    handleClearChat,
    stopGeneration,
    lastUserMessage,
  }
}
