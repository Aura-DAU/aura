"use client"

import { useEffect, useRef, useState } from "react"
import { BrandMark } from "@/components/ui/brand-mark"

interface StreamingIndicatorProps {
  thinkingStep?: string
}

// Playful, on-brand loading messages shown while AURA works on a response.
// These rotate automatically whenever the backend hasn't sent a specific
// step name (thinkingStep is undefined, or still the generic placeholder
// "Thinking…" set as soon as a request goes out). If a real backend step
// name is ever streamed in (e.g. "Searching knowledge base…"), that value
// takes priority and the rotation pauses on it.
const DEFAULT_LOADING_MESSAGES = [
  "Thinking…",
  "Digging through the knowledge base…",
  "Flipping through the handbook…",
  "Cross-referencing DAU records…",
  "Consulting the registrar…",
  "Checking the campus files…",
  "Scanning the syllabus…",
  "Piecing it together…",
  "Double-checking the details…",
  "Almost there…",
]

const ROTATION_INTERVAL_MS = 2200

export function StreamingIndicator({ thinkingStep }: StreamingIndicatorProps) {
  const [messageIndex, setMessageIndex] = useState(0)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const hasCustomStep = Boolean(thinkingStep) && thinkingStep !== "Thinking…"

  useEffect(() => {
    if (hasCustomStep) {
      // A specific backend-provided step is being shown — stop rotating.
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    intervalRef.current = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % DEFAULT_LOADING_MESSAGES.length)
    }, ROTATION_INTERVAL_MS)

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [hasCustomStep])

  const displayText = hasCustomStep ? thinkingStep : DEFAULT_LOADING_MESSAGES[messageIndex]

  return (
    <div className="msg-enter flex items-start gap-3">
      <BrandMark className="mt-0.5 size-8" isActive />
      <div className="flex min-h-9 items-center gap-2.5 pt-1">
        <div className="flex items-center gap-1" aria-hidden="true">
          <span className="chat-v2-dot size-1.5 rounded-full bg-theme-red" style={{ animationDelay: "0ms" }} />
          <span className="chat-v2-dot size-1.5 rounded-full bg-theme-yellow" style={{ animationDelay: "150ms" }} />
          <span className="chat-v2-dot size-1.5 rounded-full bg-theme-red" style={{ animationDelay: "300ms" }} />
        </div>
        <span
          key={displayText}
          className="text-shimmer loading-msg-fade text-sm font-medium"
        >
          {displayText}
        </span>
        <span className="sr-only">AURA is responding</span>
      </div>
    </div>
  )
}
