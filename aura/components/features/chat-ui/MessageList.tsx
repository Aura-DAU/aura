"use client"

import { useCallback, useEffect, useRef, useState } from "react"
import { ArrowDown } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatMessage, Citation } from "@/lib/chat-types"
import { Message } from "./Message"
import { StreamingIndicator } from "./StreamingIndicator"

interface MessageListProps {
  messages: ChatMessage[]
  loading: boolean
  thinkingStep?: string
  activeCitations: Citation[]
  onRegenerate: () => void
}

export function MessageList({
  messages,
  loading,
  thinkingStep,
  activeCitations,
  onRegenerate,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const stickToBottomRef = useRef(true)
  const [showScrollButton, setShowScrollButton] = useState(false)
  const lastAssistantIndex = messages.findLastIndex((m) => m.role === "assistant")
  const showIndicator = loading && messages[messages.length - 1]?.role !== "assistant"

  useEffect(() => {
    const el = containerRef.current?.parentElement
    if (!el) return

    const onScroll = () => {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
      stickToBottomRef.current = distanceFromBottom < 120
      setShowScrollButton(distanceFromBottom > 240)
    }

    el.addEventListener("scroll", onScroll, { passive: true })
    return () => el.removeEventListener("scroll", onScroll)
  }, [])

  const scrollToBottom = useCallback(() => {
    stickToBottomRef.current = true
    setShowScrollButton(false)
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [])

  useEffect(() => {
    if (!stickToBottomRef.current) return
    bottomRef.current?.scrollIntoView({
      behavior: loading ? "auto" : "smooth",
      block: "end",
    })
  }, [messages, loading, thinkingStep])

  return (
    <div ref={containerRef} className="relative mx-auto w-full max-w-3xl 2xl:max-w-5xl px-4 py-6 md:py-8" aria-live="polite" aria-atomic="false">
      <div className="space-y-8">
        {messages.map((message, index) => {
          const isStreaming =
            loading && index === lastAssistantIndex && message.role === "assistant"
          const isLatestAssistant =
            message.role === "assistant" && index === lastAssistantIndex && !loading
          return (
            <Message
              key={`${message.timestamp ?? index}-${message.role}-${index}`}
              message={message}
              isStreaming={isStreaming}
              showActions={isLatestAssistant}
              citations={index === lastAssistantIndex ? activeCitations : undefined}
              onRegenerate={isLatestAssistant ? onRegenerate : undefined}
            />
          )
        })}
        {showIndicator ? <StreamingIndicator thinkingStep={thinkingStep} /> : null}
        <div ref={bottomRef} className="h-2" />
      </div>

      <div className="pointer-events-none sticky bottom-3 z-10 h-0">
        <button
          type="button"
          onClick={scrollToBottom}
          aria-label="Scroll to latest message"
          aria-hidden={!showScrollButton}
          tabIndex={showScrollButton ? 0 : -1}
          className={cn(
            "absolute bottom-0 left-1/2 inline-flex size-9 -translate-x-1/2 items-center justify-center rounded-full border border-theme-gray-light bg-theme-gray/90 text-neutral-300 shadow-[0_8px_24px_-8px_rgba(0,0,0,0.9)] backdrop-blur-md transition-all duration-200",
            "hover:border-theme-gray-lighter hover:text-neutral-100 active:scale-90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/35",
            showScrollButton
              ? "pointer-events-auto scale-100 opacity-100"
              : "pointer-events-none scale-90 opacity-0",
          )}
        >
          <ArrowDown className="size-4" />
        </button>
      </div>
    </div>
  )
}
