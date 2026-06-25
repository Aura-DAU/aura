"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import type {
  ChatMessage,
  ChatThread,
  Citation,
  StudentProfile,
  UserSession,
} from "@/lib/chat-types"

const STORAGE_KEY  = "aura-threads-v2"
const PROFILE_KEY  = "aura-profile-v2"
const SESSION_KEY  = "aura-session-v1"

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
  return messages.map(({ role, content }) => ({ role, content }))
}

// Fire-and-forget — never blocks the UI
function saveHistoryToServer(
  email: string,
  threads: (StoredThread & { messages: ChatMessage[] })[]
): void {
  const payload = threads.slice(0, 10)
  fetch("/api/auth/history", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, threads: payload }),
  }).catch(() => { /* ignore network errors */ })
}

async function* parseSSEStream(response: Response) {
  if (!response.body) throw new Error("No response body")
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
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
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [activeCitations, setActiveCitations] = useState<Citation[]>([])
  const [studentProfile, setStudentProfile] = useState<StudentProfile>(DEFAULT_PROFILE)
  const [userSession, setUserSession] = useState<UserSession | null>(null)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const hydrated = useRef(false)

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
      const rawSession = localStorage.getItem(SESSION_KEY)
      if (rawSession) setUserSession(JSON.parse(rawSession) as UserSession)
    } catch {
      /* ignore corrupt storage */
    }
    hydrated.current = true
  }, [])

  useEffect(() => {
    if (!hydrated.current) return
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(threads))
    } catch {
      /* quota or unavailable */
    }
  }, [threads])

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
      setActiveThreadIdState(id)
      const thread = threads.find((t) => t.id === id)
      setMessages(thread ? thread.messages : [])
      setActiveCitations([])
      setErrorMessage(null)
    },
    [threads],
  )

  const startNewChat = useCallback(() => {
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
      if (!trimmed || loading) return

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
        const response = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            question: trimmed,
            history: toBackendHistory(messages),
            studentProfile: toBackendProfile(studentProfile),
          }),
        })

        if (!response.ok || !response.body) {
          throw new Error("Request failed")
        }

        let assistantText = ""
        let citations: Citation[] = []
        const assistantMsg: ChatMessage = {
          role: "assistant",
          content: "",
          timestamp: Date.now(),
        }
        setMessages([...baseMessages, assistantMsg])

        for await (const chunk of parseSSEStream(response)) {
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
          }
        }

        const finalMessages: ChatMessage[] = [
          ...baseMessages,
          { ...assistantMsg, content: assistantText },
        ]
        persistMessages(threadId, finalMessages)

        // Sync to server (fire-and-forget) if a user is logged in
        try {
          const rawSession = localStorage.getItem(SESSION_KEY)
          if (rawSession) {
            const session = JSON.parse(rawSession) as { email: string }
            if (session.email) {
              // Build latest snapshot of threads to sync
              setThreads((current) => {
                saveHistoryToServer(session.email, current)
                return current
              })
            }
          }
        } catch { /* ignore */ }
      } catch {
        setErrorMessage("Something went wrong. Please try again.")
        setMessages(baseMessages)
      } finally {
        setLoading(false)
        setThinkingStep(undefined)
      }
    },
    [activeThreadId, loading, messages, persistMessages, studentProfile],
  )

  const handleClearChat = useCallback(() => {
    if (activeThreadId) {
      persistMessages(activeThreadId, [])
    }
    setMessages([])
    setActiveCitations([])
    setErrorMessage(null)
  }, [activeThreadId, persistMessages])

  const transcribeAudio = useCallback(
    async (blob: Blob) => {
      setIsTranscribing(true)
      try {
        const form = new FormData()
        form.append("audio", blob, "recording.webm")
        const res = await fetch("/api/speech", { method: "POST", body: form })
        const data = (await res.json()) as { text?: string; error?: string }
        const transcript = data.text
        if (transcript) {
          setInputText((prev) => (prev ? `${prev} ${transcript}` : transcript))
        } else {
          setErrorMessage(data.error ?? "Could not transcribe audio.")
        }
      } catch {
        setErrorMessage("Could not transcribe audio.")
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
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const recorder = new MediaRecorder(stream)
      audioChunksRef.current = []
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data)
      }
      recorder.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" })
        void transcribeAudio(blob)
      }
      mediaRecorderRef.current = recorder
      recorder.start()
      setIsRecording(true)
    } catch {
      setErrorMessage("Microphone access was denied.")
    }
  }, [isRecording, transcribeAudio])

  const logout = useCallback(async () => {
    setUserSession(null)
    try { localStorage.removeItem(SESSION_KEY) } catch { /* ignore */ }
  }, [])

  return {
    messages,
    inputText,
    setInputText,
    loading,
    thinkingStep,
    isRecording,
    isTranscribing,
    errorMessage,
    setErrorMessage,
    activeCitations,
    threads: threads.map(({ id, title }) => ({ id, title })),
    activeThreadId,
    setActiveThreadId,
    startNewChat,
    deleteThread,
    studentProfile,
    saveProfile,
    handleMicClick,
    handleSendMessage,
    handleClearChat,
    userSession,
    logout,
  }
}
