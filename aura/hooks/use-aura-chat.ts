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
import { AppError, ErrorCode, isAbortError, sanitizePublicMessage } from "@/lib/errors"
import { toCalendarSyncAction } from "@/components/features/chat-ui/calendar-sync-presentation"

/** Soft failure copy the pipeline sometimes returns as a normal answer. */
const SOFT_FAILURE_ANSWER =
  /i'?m having trouble (retrieving information|reaching the student records)/i

const STREAM_ERROR_FALLBACK =
  "Something went wrong while processing your request. Please try again."

const STORAGE_KEY  = "aura-threads-v2"
const PROFILE_KEY  = "aura-profile-v2"
const ACTIVE_THREAD_KEY = "aura-active-thread-v2"

interface StoredThread extends ChatThread {
  messages: ChatMessage[]
}

const DEFAULT_PROFILE: StudentProfile = {
  name: "",
  program: "",
  year: "",
  interests: "",
}

/**
 * Dept codes resolved server-side from the student's ERP id (see
 * server/api/identity_routes.py / academic_scope_persist.py) mapped to the
 * same display labels the RAG pipeline uses (retrieval_pipeline.py). Used to
 * auto-fill the profile modal's Program field so a student never has to type
 * something the system already knows from their ERP id.
 */
const DEPT_TO_PROGRAM_LABEL: Record<string, string> = {
  ICT: "B.Tech. (ICT)",
  ICTCS: "B.Tech. (ICT)",
  MnC: "B.Tech. (MnC)",
  EVD: "B.Tech. (EVD)",
  MTech: "M.Tech. (ICT)",
  MScIT: "M.Sc. (IT)",
  MScDS: "M.Sc. (Data Science)",
  PhD: "Ph.D.",
}

function ordinalYearLabel(year: number): string {
  const suffix =
    year === 1 ? "st" : year === 2 ? "nd" : year === 3 ? "rd" : "th"
  return `${year}${suffix} year`
}

function uid(): string {
  return Math.random().toString(36).slice(2, 10)
}

function deriveTitle(text: string): string {
  const clean = text.trim().replace(/\s+/g, " ")
  return clean.length > 40 ? `${clean.slice(0, 40)}…` : clean || "New chat"
}

/** Last-activity timestamp for sidebar ordering / server merge. */
function threadUpdatedAt(messages: ChatMessage[] | undefined, fallback = Date.now()): number {
  if (!messages || messages.length === 0) return fallback
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

/** Seconds to wait after a load shed when no usable Retry-After is present. */
const DEFAULT_RETRY_AFTER_SECONDS = 5

export interface ShedSignal {
  /** Which layer shed the request — the edge (429) or backend admission (503). */
  shedBy: "edge" | "backend"
  retryAfterSeconds: number
}

export function parseRetryAfterSeconds(
  value: string | null | undefined,
  fallback = DEFAULT_RETRY_AFTER_SECONDS,
): number {
  if (!value) return fallback
  const seconds = Number(value)
  if (Number.isFinite(seconds) && seconds > 0) return Math.ceil(seconds)
  const at = Date.parse(value)
  if (!Number.isNaN(at)) {
    const delta = Math.ceil((at - Date.now()) / 1000)
    if (delta > 0) return delta
  }
  return fallback
}

/**
 * Distinguishes a capacity shed from the per-identity question quota.
 *
 * The edge sheds with 429 + `EDGE_OVERLOADED` / `X-Aura-Shed-By: edge` and
 * backend admission with 503 + `ADMISSION_OVERLOADED` / `X-Aura-Shed-By:
 * backend`; a real quota exhaustion is a 429 carrying neither. Treating every
 * 429 as quota would zero a guest's counter for the rest of the day over what
 * is actually a transient overload they can retry in seconds.
 *
 * Pass a clone — this consumes the body.
 */
export async function readShedSignal(res: Response): Promise<ShedSignal | null> {
  if (res.status !== 429 && res.status !== 503) return null

  let payload: { code?: string; shedBy?: string; retryAfter?: number } | null = null
  try {
    payload = (await res.json()) as { code?: string; shedBy?: string; retryAfter?: number }
  } catch {
    payload = null
  }

  const shedBy = res.headers.get("X-Aura-Shed-By") ?? payload?.shedBy
  const code = payload?.code
  const isOverload =
    code === "EDGE_OVERLOADED" ||
    code === "ADMISSION_OVERLOADED" ||
    shedBy === "edge" ||
    shedBy === "backend"
  if (!isOverload) return null

  const bodyRetry =
    typeof payload?.retryAfter === "number" && payload.retryAfter > 0
      ? Math.ceil(payload.retryAfter)
      : DEFAULT_RETRY_AFTER_SECONDS

  return {
    shedBy: shedBy === "backend" ? "backend" : "edge",
    retryAfterSeconds: parseRetryAfterSeconds(res.headers.get("Retry-After"), bodyRetry),
  }
}

export function shedErrorFor(shed: ShedSignal): AppError {
  const s = shed.retryAfterSeconds
  return new AppError({
    code: ErrorCode.BACKEND_UNAVAILABLE,
    message: `AURA is busy right now — please retry in ${s} second${s === 1 ? "" : "s"}.`,
    detail: `shed_by=${shed.shedBy}`,
  })
}

/**
 * Index into `priorMessages` for the start of the unsummarised tail.
 *
 * Always `priorSummaryCount` (clamped to the transcript). Never advance past it:
 * a turn past that pointer is not yet in the summary, so skipping it here would
 * drop it from the model's context entirely. Compaction of an over-long
 * unsummarised span is the backend's job (`AURA_MAX_TAIL_TURNS`); this helper
 * must not invent a second, silent drop.
 */
export function computeHistoryTailStart(
  priorSummaryCount: number,
  priorMessageCount: number,
): number {
  return Math.min(Math.max(priorSummaryCount, 0), priorMessageCount)
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
 * Drops this conversation's block from the backend's persistent per-user
 * memory. Clearing or deleting a chat has to reach storage: the block is keyed
 * by thread id and otherwise survives for the full retention window (90 days by
 * default), still being injected into later conversations. Guests are a no-op —
 * they have no stored memory. Failures are surfaced, because silently keeping
 * memory the user asked to delete is a privacy problem, not a cosmetic one.
 */
function requestThreadMemoryDelete(threadId: string): Promise<Response> {
  return apiFetch(`/api/memory?threadId=${encodeURIComponent(threadId)}`, {
    method: "DELETE",
  })
}

function forgetThreadMemory(threadId: string): void {
  requestThreadMemoryDelete(threadId)
    .then((res) => {
      if (res.ok) return
      // One retry after a short delay — the chat is already gone from the
      // user's chat list by the time this runs, so a single transient
      // network/backend blip shouldn't read as a failed deletion.
      return new Promise((resolve) => setTimeout(resolve, 1200))
        .then(() => requestThreadMemoryDelete(threadId))
        .then((retryRes) => {
          if (!retryRes.ok) {
            toastError("The chat was deleted, but its saved memory couldn't be cleared. Please try again.")
          }
        })
    })
    .catch(() => {
      return new Promise((resolve) => setTimeout(resolve, 1200))
        .then(() => requestThreadMemoryDelete(threadId))
        .catch(() => {
          toastError("The chat was deleted, but its saved memory couldn't be cleared. Please try again.")
        })
    })
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
  const loadingRef = useRef(false)

  useEffect(() => {
    activeThreadIdRef.current = activeThreadId
  }, [activeThreadId])

  useEffect(() => {
    loadingRef.current = loading
  }, [loading])

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
        const parsed = (JSON.parse(rawThreads) as StoredThread[]).map((t) => {
          const safeMessages = Array.isArray(t.messages) ? t.messages : []
          return {
            ...t,
            messages: safeMessages,
            updatedAt: t.updatedAt ?? threadUpdatedAt(safeMessages, 0),
          }
        })
        const sorted = sortThreadsByRecency(parsed)
        const storedActiveId = localStorage.getItem(ACTIVE_THREAD_KEY)
        const initialThread =
          storedActiveId === ""
            ? undefined
            : storedActiveId
              ? sorted.find((thread) => thread.id === storedActiveId) ?? sorted[0]
              : sorted[0]
        // eslint-disable-next-line react-hooks/set-state-in-effect
        setThreads(sorted)
        if (initialThread) {
          setActiveThreadIdState(initialThread.id)
          setMessages(initialThread.messages)
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
                const safeMessages = Array.isArray(t.messages) ? t.messages : []
                map.set(t.id, {
                  ...t,
                  messages: safeMessages,
                  updatedAt: t.updatedAt ?? threadUpdatedAt(safeMessages, 0),
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
              } else if (activeId && !loadingRef.current) {
                // Only replace the open transcript when the merge actually
                // chose a newer copy. Never clobber while a reply is streaming.
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
    if (!hasHydrated) return
    try {
      localStorage.setItem(ACTIVE_THREAD_KEY, activeThreadId ?? "")
    } catch {
      /* unavailable */
    }
  }, [activeThreadId, hasHydrated])

  // Auto-fill Program/Year from the student's verified ERP identity
  // (department + currentYear, resolved server-side from their ERP id at
  // login — see server/api/identity_routes.py). Only fills fields the
  // student hasn't already set themselves, and only once per field, so an
  // edit they save is never silently overwritten on a later session.
  useEffect(() => {
    if (!hasHydrated) return
    const dept = session?.user?.department
    const year = session?.user?.currentYear
    const programLabel = dept ? DEPT_TO_PROGRAM_LABEL[dept] : undefined
    const yearLabel = typeof year === "number" ? ordinalYearLabel(year) : undefined
    if (!programLabel && !yearLabel) return

    // eslint-disable-next-line react-hooks/set-state-in-effect
    setStudentProfile((prev) => {
      if (prev.program && prev.year) return prev
      const next = {
        ...prev,
        program: prev.program || programLabel || prev.program,
        year: prev.year || yearLabel || prev.year,
      }
      if (next.program === prev.program && next.year === prev.year) return prev
      try {
        localStorage.setItem(PROFILE_KEY, JSON.stringify(next))
      } catch {
        /* ignore */
      }
      return next
    })
  }, [hasHydrated, session?.user?.department, session?.user?.currentYear])

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
      loadingRef.current = false
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
    loadingRef.current = false
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
      forgetThreadMemory(id)
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

  const insertGreeting = useCallback((text: string) => {
    const existing = threads.find(
      (thread) =>
        thread.messages.length === 1 &&
        thread.messages[0]?.role === "assistant" &&
        thread.messages[0].content === text,
    )
    if (existing) {
      setActiveThreadIdState(existing.id)
      setMessages(existing.messages)
      return
    }

    const threadId = uid()
    const msg: ChatMessage = { role: "assistant", content: text, timestamp: Date.now() }
    const newThread: StoredThread = {
      id: threadId,
      title: "Welcome to AURA",
      messages: [msg],
      updatedAt: msg.timestamp,
    }
    setThreads((prev) => sortThreadsByRecency([newThread, ...prev]))
    setActiveThreadIdState(threadId)
    setMessages([msg])
  }, [threads])

  const handleSendMessage = useCallback(
    async (text: string, options?: { regenerate?: boolean }) => {
      const trimmed = text.trim()
      if (!trimmed || loadingRef.current || remainingQuota === 0) return

      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      loadingRef.current = true
      setLoading(true)
      setThinkingStep("Thinking…")
      setErrorMessage(null)
      setActiveCitations([])
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
      // Strip trailing assistant turns first: handleRegenerate calls setState
      // then send in the same tick, so `messages` here can still include the
      // old reply (stale closure).
      let baseMessages: ChatMessage[]
      if (options?.regenerate) {
        if (!threadId) {
          loadingRef.current = false
          setLoading(false)
          setThinkingStep(undefined)
          return
        }
        let transcript = priorMessages
        while (
          transcript.length > 0 &&
          transcript[transcript.length - 1]?.role === "assistant"
        ) {
          transcript = transcript.slice(0, -1)
        }
        const last = transcript[transcript.length - 1]
        if (last?.role === "user" && last.content.trim() === trimmed) {
          baseMessages = transcript
          priorMessages = transcript.slice(0, -1)
        } else {
          baseMessages = [...transcript, userMsg]
          priorMessages = transcript
        }
        persistMessages(threadId, baseMessages)
      } else {
        baseMessages = [...priorMessages, userMsg]
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

      // Rolling memory: send the running summary plus every turn after it. The
      // start must never move past priorSummaryCount — a turn skipped here is in
      // neither the summary nor the tail, so it disappears from the model's
      // context with no user-visible signal. The backend compacts an over-long
      // tail itself (ConversationMemory.prepare folds once the span passes
      // AURA_MAX_TAIL_TURNS, well under the API's 20-turn history cap) and
      // reports foldedTurns so this pointer advances on the next request.
      const activeThread = threads.find((t) => t.id === threadId)
      const priorSummaryCount = activeThread?.summaryTurnCount ?? 0
      const threadSummary = activeThread?.summary
      const tailStart = computeHistoryTailStart(priorSummaryCount, priorMessages.length)
      const tail = priorMessages.slice(tailStart)

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

        if (!response.ok || !response.body) {
          // A capacity shed (edge 429 EDGE_OVERLOADED / backend 503
          // ADMISSION_OVERLOADED) is retryable and says nothing about how many
          // questions the user has left — it must not touch the quota counter.
          const shed = response.ok ? null : await readShedSignal(response.clone())
          if (shed) {
            throw shedErrorFor(shed)
          }
          if (response.status === 429) {
            // Genuine quota exhaustion. Only pin the guest counter to 0;
            // signed-in users are unlimited, so a transient 429 must not
            // permanently lock the composer.
            if (!session?.user) {
              setRemainingQuotaState(0)
            }
            throw AppError.rateLimited()
          }
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
        let streamErrorMessage: string | null = null
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
            const syncAction = toCalendarSyncAction(assistantText)
            if (syncAction) {
              calendarAction = syncAction
              if (syncAction.type === "timetable_sync") {
                assistantText = "Syncing your timetable with Google Calendar."
              }
            }
            setMessages((prev) => {
              const next = [...prev]
              next[next.length - 1] = {
                ...assistantMsg,
                content: assistantText,
                calendar_action: calendarAction,
              }
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
          } else if (chunk.type === "error") {
            const errCode = typeof chunk.code === "string" ? chunk.code : "RAG_ERROR"
            const errDetail = typeof chunk.detail === "string" ? chunk.detail : ""
            console.error(`[useAuraChat] Stream error (${errCode}):`, errDetail)
            // Prefer an explicit safe `message` if the BFF/backend adds one;
            // never surface raw `detail` (stack / infra strings).
            const fromChunk =
              typeof chunk.message === "string"
                ? sanitizePublicMessage(chunk.message)
                : undefined
            streamErrorMessage = fromChunk ?? STREAM_ERROR_FALLBACK
          } else if (chunk.type === "profile-update" && chunk.profile && chunk.profile.name) {
            setStudentProfile(prev => {
              const next = { ...prev, name: chunk.profile.name }
              try { localStorage.setItem(PROFILE_KEY, JSON.stringify(next)) } catch {}
              return next
            })
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

        // Empty reply or mid-stream failure with no usable text — roll back the
        // blank assistant bubble and surface a clear, actionable error.
        if (!assistantText.trim() && !calendarAction) {
          const msg = streamErrorMessage ?? STREAM_ERROR_FALLBACK
          setErrorMessage(msg)
          toastError(msg)
          setMessages(baseMessages)
          persistMessages(threadId, baseMessages)
          return
        }

        if (streamErrorMessage) {
          // Partial tokens before failure — surface clearly. When the backend
          // already streamed an apology delta, skip toast/banner spam.
          const bubbleIsApology =
            assistantText.trim() === streamErrorMessage ||
            /sorry, i encountered an error/i.test(assistantText)
          if (!bubbleIsApology) {
            setErrorMessage(streamErrorMessage)
            toastError(streamErrorMessage)
          }
        } else if (SOFT_FAILURE_ANSWER.test(assistantText)) {
          // Pipeline returned a soft-failure sentence as the answer. Keep the
          // copy in-thread; banner nudges the user toward regenerate.
          setErrorMessage(
            "I couldn't retrieve that information. You can try regenerating the reply.",
          )
        }

        const finalMessages: ChatMessage[] = [
          ...baseMessages,
          {
            ...assistantMsg,
            content: assistantText,
            is_personal_data: isPersonalData || undefined,
            calendar_action: calendarAction,
            citations: citations.length > 0 ? citations : undefined,
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
          loadingRef.current = false
          setLoading(false)
          setThinkingStep(undefined)
        }
      }
    },
    [activeThreadId, messages, threads, persistMessages, studentProfile, session, remainingQuota, decrementQuota, syncQuotaFromServer, syncThreadsToServer],
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
      forgetThreadMemory(activeThreadId)
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
    loadingRef.current = false
    setLoading(false)
    setThinkingStep(undefined)
    // Drop an empty assistant placeholder (stop before first token). Persist
    // any partial text so a thread switch does not lose it.
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      if (!last || last.role !== "assistant") return prev
      const tid = activeThreadIdRef.current
      if (!last.content.trim()) {
        const next = prev.slice(0, -1)
        if (tid) persistMessages(tid, next)
        return next
      }
      if (tid) persistMessages(tid, prev)
      return prev
    })
  }, [persistMessages])

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
    insertGreeting,
    hasHydrated,
  }
}
