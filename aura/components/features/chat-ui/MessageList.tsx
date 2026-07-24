"use client"

import { useEffect, useRef } from "react"
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
  const lastAssistantIndex = messages.findLastIndex((m) => m.role === "assistant")
  const showIndicator = loading && messages[messages.length - 1]?.role !== "assistant"

  useEffect(() => {
    const el = containerRef.current?.parentElement
    if (!el) return

    const onScroll = () => {
      const distanceFromBottom = el.scrollHeight - el.scrollTop - el.clientHeight
      stickToBottomRef.current = distanceFromBottom < 120
    }

    el.addEventListener("scroll", onScroll, { passive: true })
    return () => el.removeEventListener("scroll", onScroll)
  }, [])

  useEffect(() => {
    if (!stickToBottomRef.current) return
    bottomRef.current?.scrollIntoView({
      behavior: loading ? "auto" : "smooth",
      block: "end",
    })
  }, [messages, loading, thinkingStep])

  return (
    <div ref={containerRef} className="mx-auto w-full max-w-3xl space-y-8 px-4 py-6 md:py-8">
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
  )
}
