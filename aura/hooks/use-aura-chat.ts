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
import { getUserMessage, toastAppError, toastError, appErrorFromResponse } from "@/lib/toast"
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

function toBackendProfile(p: StudentProfile) {
  const out: Record<string, string> = {}
  if (p.name) out.name = p.name
  if (p.program) out.branch = p.program
  if (p.year) out.year = p.year
  if (p.interests) out.interests = p.interests
  return Object.keys(out).length ? out : undefined
}

function toBackendHistory(messages: ChatMessage[]) {
  return messages.slice(-6).map(({ role, content }) => ({ role, content }))
}

// Fire-and-forget — never blocks the UI
function saveHistoryToServer(
  email: string,
  threads: (StoredThread & { messages: ChatMessage[] })[]
): void {
  const payload = threads.slice(0, 10)
  apiFetch("/api/auth/history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, threads: payload }),
  }).catch(() => { /* ignore network errors */ })
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
  const { data: session } = useSession()

  useEffect(() => {
    if (session?.user) {
      const email = session.user.email || 'guest'
      const role = session.user.role || 'guest'
      const maxQuota = role === 'guest' ? 3 : 5
      const date = new Date().toISOString().split('T')[0]
      const key = `aura-quota-${email}`
      
      try {
        const stored = localStorage.getItem(key)
        if (stored) {
          const parsed = JSON.parse(stored)
          if (parsed.date === date) {
            setRemainingQuotaState(Math.max(0, maxQuota - parsed.count))
          } else {
            setRemainingQuotaState(maxQuota)
            localStorage.setItem(key, JSON.stringify({ date, count: 0 }))
          }
        } else {
          setRemainingQuotaState(maxQuota)
          localStorage.setItem(key, JSON.stringify({ date, count: 0 }))
        }
      } catch {
        setRemainingQuotaState(maxQuota)
      }
    } else {
      setRemainingQuotaState(null)
    }
  }, [session])

  const decrementQuota = useCallback(() => {
    setRemainingQuotaState(prev => {
      if (prev === null) return null;
      const newVal = Math.max(0, prev - 1)
      if (session?.user) {
        const email = session.user.email || 'guest'
        const role = session.user.role || 'guest'
        const maxQuota = role === 'guest' ? 3 : 5
        const date = new Date().toISOString().split('T')[0]
        const key = `aura-quota-${email}`
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
  const lastVolumeUpdateRef = useRef(0)
  const mountedRef = useRef(true)

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
        const parsed = JSON.parse(rawThreads) as StoredThread[]
        setThreads(parsed)
        if (parsed[0]) {
          setActiveThreadIdState(parsed[0].id)
          setMessages(parsed[0].messages)
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
      setThreads((prev) =>
        prev.map((t) =>
          t.id === threadId
            ? { ...t, messages: next, title: title ?? t.title }
            : t,
        ),
      )
    },
    [],
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
        return next
      })
    },
    [activeThreadId],
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
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed || loading || remainingQuota === 0) return

      abortRef.current?.abort()
      const controller = new AbortController()
      abortRef.current = controller

      setErrorMessage(null)
      setInputText("")

      let threadId = activeThreadId
      const userMsg: ChatMessage = {
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      }

      if (!threadId) {
        threadId = uid()
        const newThread: StoredThread = {
          id: threadId,
          title: deriveTitle(trimmed),
          messages: [userMsg],
        }
        setThreads((prev) => [newThread, ...prev])
        setActiveThreadIdState(threadId)
      }

      const baseMessages = [...messages, userMsg]
      setMessages(baseMessages)
      persistMessages(threadId, baseMessages, deriveTitle(messages[0]?.content ?? trimmed))

      setLoading(true)
      setThinkingStep("Thinking…")

      try {
        const response = await apiFetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: trimmed,
            history: toBackendHistory(messages),
            studentProfile: toBackendProfile(studentProfile),
          }),
          signal: controller.signal,
        })

        if (controller.signal.aborted || !mountedRef.current) return

        if (response.status === 429) {
          setRemainingQuotaState(0)
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

        if (session?.user?.email) {
          setThreads((current) => {
            saveHistoryToServer(session.user.email!, redactPersonalDataMessages(current))
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
    [activeThreadId, loading, messages, persistMessages, studentProfile, session, remainingQuota, decrementQuota],
  )

  const handleClearChat = useCallback(() => {
    if (activeThreadId) {
      persistMessages(activeThreadId, [])
    }
    setMessages([])
    setActiveCitations([])
    setErrorMessage(null)
  }, [activeThreadId, persistMessages])

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
    () => threads.map(({ id, title }) => ({ id, title })),
    [threads],
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
    activeThreadId,
    setActiveThreadId,
    startNewChat,
    deleteThread,
    studentProfile,
    saveProfile,
    handleMicClick,
    handleSendMessage,
    handleClearChat,
    stopGeneration,
    lastUserMessage,
  }
}
