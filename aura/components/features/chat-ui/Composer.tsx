"use client"

import { type FormEvent, type KeyboardEvent, useEffect, useState } from "react"
import TextareaAutosize from "react-textarea-autosize"
import { ArrowUp, Mic, Square, Loader2 } from "lucide-react"
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
  onStop?: () => void
  remainingQuota?: number | null
  /** "docked" pins to the bottom with a fade; "centered" sits inline in the welcome view. */
  variant?: "docked" | "centered"
}

function detectMicSupport(): boolean {
  return (
    typeof navigator !== "undefined" &&
    typeof navigator.mediaDevices?.getUserMedia === "function" &&
    typeof window !== "undefined" &&
    "MediaRecorder" in window
  )
}

export function Composer({
  inputText,
  setInputText,
  loading,
  isRecording,
  isTranscribing,
  recordingVolume = 0,
  onSend,
  onMicClick,
  onStop,
  remainingQuota = null,
  variant = "docked",
}: ComposerProps) {
  const [showMic, setShowMic] = useState(false)
  const { data: session, status } = useSession()

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- client-only MediaRecorder probe
    setShowMic(detectMicSupport())
  }, [])

  const isUnauthenticated = status === "unauthenticated"
  // Guests (unauthenticated) can send until their daily quota hits 0.
  // Signed-in @dau.ac.in accounts have unlimited quota, so remainingQuota
  // is always null for them and this never blocks sending.
  const quotaExhausted = remainingQuota === 0
  const canSend = inputText.trim().length > 0 && !loading && !isRecording && !quotaExhausted
  const nearLimit = inputText.length >= MAX_CHARS * 0.9
  const atLimit = inputText.length >= MAX_CHARS
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
    <div
      className={cn(
        "relative",
        variant === "docked" &&
          "bg-gradient-to-t from-theme-black via-theme-black/92 to-transparent pt-3",
      )}
    >
      <form
        onSubmit={handleSubmit}
        className={cn(
          "w-full",
          variant === "docked" && "mx-auto max-w-3xl 2xl:max-w-5xl px-4 pb-3 md:pb-4",
        )}
      >
        {quotaExhausted ? (
          <div className="flex flex-col items-center justify-center rounded-[26px] border border-theme-gray-light bg-theme-gray/80 px-4 py-7 text-center shadow-[0_18px_50px_-24px_rgba(0,0,0,0.9)] backdrop-blur-xl">
            <p className="mb-3.5 text-sm text-neutral-400">
              {isUnauthenticated
                ? "You've used all your free questions for today."
                : "Question limit reached."}
            </p>
            {isUnauthenticated ? (
              <a
                href="/login"
                className="inline-flex h-9 items-center justify-center gap-1.5 rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-5 text-sm font-semibold text-black transition-all hover:brightness-110 active:scale-[0.98]"
              >
                Sign in with @dau.ac.in for unlimited access
              </a>
            ) : (
              <p className="text-xs text-neutral-400">Please try again tomorrow.</p>
            )}
          </div>
        ) : (
          <div
            className={cn(
              "composer-shell group relative rounded-[26px] border bg-theme-gray/95 px-2.5 pb-2 pt-1.5 backdrop-blur-xl transition-all duration-300",
              "border-theme-gray-light shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04),0_18px_50px_-22px_rgba(0,0,0,0.9)]",
              "focus-within:border-theme-gray-lighter focus-within:shadow-[0_0_0_1px_rgba(255,190,63,0.22),0_22px_56px_-20px_rgba(0,0,0,0.95)]",
              isRecording && "border-theme-red/50 focus-within:border-theme-red/50 focus-within:shadow-[0_0_0_1px_rgba(244,80,59,0.3),0_22px_56px_-20px_rgba(0,0,0,0.95)]",
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
              className="chat-v2-scroll block w-full resize-none bg-transparent px-2 pb-1.5 pt-2 text-[15px] leading-relaxed text-neutral-100 outline-none placeholder:text-neutral-400"
            />

            <div className="flex items-center justify-between gap-2 pl-2">
              <div className="flex min-w-0 items-center gap-1.5 text-[11px] text-neutral-600">
                {atLimit || nearLimit ? (
                  <span className={cn("tabular-nums", atLimit ? "text-theme-red" : "text-neutral-500")}>
                    {inputText.length.toLocaleString()}/{MAX_CHARS.toLocaleString()}
                  </span>
                ) : remainingQuota !== null ? (
                  <span className={cn(remainingQuota === 0 ? "text-theme-red" : "text-neutral-600")}>
                    {remainingQuota} {remainingQuota === 1 ? "message" : "messages"} left
                  </span>
                ) : (
                  <span className="hidden items-center gap-1 sm:inline-flex">
                    <kbd className="rounded border border-theme-gray-lighter/70 bg-theme-gray-light px-1 py-px font-sans text-[10px] text-neutral-400">
                      Shift + ↵
                    </kbd>
                    <span>for a new line</span>
                  </span>
                )}
              </div>

              <div className="flex shrink-0 items-center gap-1">
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
                        "relative z-10 inline-flex size-9 items-center justify-center rounded-full transition-all duration-150 disabled:opacity-50",
                        "active:scale-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/40",
                        isRecording
                          ? "bg-theme-red text-black"
                          : "text-neutral-400 hover:bg-theme-gray-light hover:text-neutral-100",
                      )}
                    >
                      {isTranscribing ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : isRecording ? (
                        <Square className="size-3.5 fill-current" />
                      ) : (
                        <Mic className="size-4" />
                      )}
                    </button>
                  </div>
                ) : null}

                {loading ? (
                  <button
                    type="button"
                    onClick={onStop}
                    aria-label="Stop generating"
                    className={cn(
                      "inline-flex size-9 items-center justify-center rounded-full bg-neutral-100 text-black transition-all duration-200",
                      "active:scale-90 hover:bg-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/40",
                    )}
                  >
                    <span className="size-2.5 rounded-[3px] bg-current" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!canSend}
                    aria-label="Send message"
                    className={cn(
                      "inline-flex size-9 items-center justify-center rounded-full transition-all duration-200",
                      "active:scale-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/40",
                      canSend
                        ? "bg-gradient-to-br from-theme-red to-theme-yellow text-black shadow-[0_4px_16px_-6px_rgba(244,80,59,0.6)] hover:brightness-110"
                        : "cursor-not-allowed bg-theme-gray-light text-neutral-600",
                    )}
                  >
                    <ArrowUp className="size-4 stroke-[2.5]" />
                  </button>
                )}
              </div>
            </div>
          </div>
        )}

        {!quotaExhausted ? (
          <p className="mt-2.5 text-center text-[11px] text-neutral-600">
            AURA can make mistakes. Verify important info.
          </p>
        ) : null}
      </form>
    </div>
  )
}
