"use client"

import { type FormEvent, type KeyboardEvent, useEffect, useState } from "react"
import TextareaAutosize from "react-textarea-autosize"
import { Mic, Send, Square, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"

const MAX_CHARS = 2000

interface ComposerProps {
  inputText: string
  setInputText: (v: string) => void
  loading: boolean
  isRecording: boolean
  isTranscribing: boolean
  onSend: (text: string) => void
  onMicClick: () => void
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
  onSend,
  onMicClick,
}: ComposerProps) {
  const [showMic, setShowMic] = useState(false)
  const canSend = inputText.trim().length > 0 && !loading && !isRecording

  useEffect(() => {
    setShowMic(micSupported())
  }, [])

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
            placeholder="Message AURA…"
            aria-label="Message AURA"
            className="flex-1 resize-none bg-transparent py-1.5 text-sm leading-relaxed text-neutral-100 outline-none placeholder:text-neutral-500"
          />

          {showMic ? (
            <button
              type="button"
              onClick={onMicClick}
              disabled={isTranscribing || loading}
              aria-label={isRecording ? "Stop recording" : "Start voice input"}
              className={cn(
                "inline-flex size-9 shrink-0 items-center justify-center rounded-full transition-colors disabled:opacity-50",
                isRecording
                  ? "animate-pulse bg-theme-red text-black"
                  : "text-neutral-400 hover:bg-theme-gray-light hover:text-neutral-100",
              )}
            >
              {isTranscribing ? (
                <Loader2 className="size-4 animate-spin" />
              ) : isRecording ? (
                <Square className="size-4" />
              ) : (
                <Mic className="size-4" />
              )}
            </button>
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
        <p className="mt-2 text-center text-xs text-neutral-500">
          AI can make mistakes. Verify important info.
        </p>
      </form>
    </div>
  )
}
