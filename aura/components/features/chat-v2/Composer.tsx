"use client"

import { type FormEvent, type KeyboardEvent } from "react"
import TextareaAutosize from "react-textarea-autosize"
import { Mic, Send, Square, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import { useSession } from "next-auth/react"

const MAX_CHARS = 2000

interface ComposerProps {
  inputText: string
  setInputText: (v: string) => void
  loading: boolean
  isRecording: boolean
  isTranscribing: boolean
  recordingVolume?: number
  onSend: (text: string) => void
  onMicClick: () => void
  remainingQuota?: number | null
}

const micSupported = () =>
  typeof navigator !== "undefined" &&
  typeof navigator.mediaDevices?.getUserMedia === "function" &&
  typeof window !== "undefined" &&
  "MediaRecorder" in window

export function Composer({
  inputText,
  setInputText,
  loading,
  isRecording,
  isTranscribing,
  recordingVolume = 0,
  onSend,
  onMicClick,
  remainingQuota = null,
}: ComposerProps) {
  const showMic = micSupported()
  const { data: session, status } = useSession()
  const isUnauthenticated = status === "unauthenticated"
  const canSend = inputText.trim().length > 0 && !loading && !isRecording && !isUnauthenticated
  const role = (session?.user?.role as string) || ""
  let dynamicPlaceholder = "Message AURA…"

  if (role === "student") {
    dynamicPlaceholder = "Ask about your timetable, attendance, or requirements..."
  } else if (role.startsWith("faculty") || role.startsWith("dean") || role === "registrar") {
    dynamicPlaceholder = "Ask about class schedule, grade submission, or mentoring..."
  } else if (role === "admin" || role === "superadmin" || role === "admin_staff") {
    dynamicPlaceholder = "Ask about administration, role bindings, or settings..."
  }

  const submit = () => {
    if (!canSend) return
    onSend(inputText)
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    submit()
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <div className="border-t border-theme-gray-light bg-theme-black/70 backdrop-blur">
      <form onSubmit={handleSubmit} className="mx-auto w-full max-w-3xl px-4 py-4">
        {isUnauthenticated ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-theme-gray-light bg-theme-gray px-3 py-6 transition-colors">
            <p className="mb-3 text-sm text-neutral-400">Sign in to ask questions</p>
            <a
              href="/login"
              className="inline-flex h-9 items-center justify-center rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-4 text-sm font-medium text-black transition-opacity hover:opacity-90"
            >
              Sign In
            </a>
          </div>
        ) : (
          <div
            className={cn(
              "flex items-end gap-2 rounded-2xl border border-theme-gray-light bg-theme-gray px-3 py-2 transition-colors",
              "focus-within:border-theme-gray-lighter",
            )}
          >
            <TextareaAutosize
              value={inputText}
              onChange={(e) => setInputText(e.target.value.slice(0, MAX_CHARS))}
              onKeyDown={handleKeyDown}
              minRows={1}
              maxRows={8}
              maxLength={MAX_CHARS}
              placeholder={dynamicPlaceholder}
              aria-label="Message AURA"
              className="flex-1 resize-none bg-transparent py-1.5 text-sm leading-relaxed text-neutral-100 outline-none placeholder:text-neutral-500"
            />

          {showMic ? (
            <div className="relative flex items-center justify-center">
              {isRecording && (
                <>
                  <div
                    className="absolute -inset-1 animate-ping rounded-full bg-theme-red/30"
                    style={{
                      transform: `scale(${1 + recordingVolume * 1.5})`,
                      opacity: 0.4 + recordingVolume * 0.6,
                    }}
                  />
                  <div
                    className="absolute -inset-2 rounded-full bg-theme-red/10 transition-transform duration-75"
                    style={{
                      transform: `scale(${1 + recordingVolume * 0.8})`,
                    }}
                  />
                </>
              )}
              <button
                type="button"
                onClick={onMicClick}
                disabled={isTranscribing || loading}
                aria-label={isRecording ? "Stop recording" : "Start voice input"}
                style={{
                  transform: isRecording
                    ? `scale(${1 + recordingVolume * 0.25})`
                    : undefined,
                }}
                className={cn(
                  "relative z-10 inline-flex size-9 shrink-0 items-center justify-center rounded-full transition-all duration-75 disabled:opacity-50",
                  isRecording
                    ? "bg-theme-red text-black"
                    : "text-neutral-400 hover:bg-theme-gray-light hover:text-neutral-100",
                )}
              >
                {isTranscribing ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : isRecording ? (
                  <Square className="size-4 animate-pulse" />
                ) : (
                  <Mic className="size-4" />
                )}
              </button>
            </div>
          ) : null}

          <button
            type="submit"
            disabled={!canSend}
            aria-label="Send message"
            className={cn(
              "inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-r from-theme-red to-theme-yellow text-black transition-opacity",
              "disabled:cursor-not-allowed disabled:opacity-40",
            )}
          >
            <Send className="size-4" />
          </button>
        </div>
        )}
        <div className="mt-2 flex items-center justify-between px-1">
          <p className="text-xs text-neutral-500">
            AI can make mistakes. Verify important info.
          </p>
          {remainingQuota !== null && !isUnauthenticated && (
            <p className={cn("text-xs", remainingQuota === 0 ? "text-theme-red" : "text-neutral-500")}>
              {remainingQuota} question{remainingQuota !== 1 ? 's' : ''} remaining
            </p>
          )}
        </div>
      </form>
    </div>
  )
}
