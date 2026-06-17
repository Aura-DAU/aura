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
  const lastAssistantIndex = messages.map((m) => m.role).lastIndexOf("assistant")
  const showIndicator = loading && messages[messages.length - 1]?.role !== "assistant"

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" })
  }, [messages, loading, thinkingStep])

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6">
      {messages.map((message, index) => (
        <Message
          key={`${message.role}-${index}-${message.timestamp ?? index}`}
          message={message}
          citations={
            index === lastAssistantIndex ? activeCitations : undefined
          }
          onRegenerate={
            message.role === "assistant" && index === lastAssistantIndex && !loading
              ? onRegenerate
              : undefined
          }
        />
      ))}
      {showIndicator ? <StreamingIndicator thinkingStep={thinkingStep} /> : null}
      <div ref={bottomRef} />
    </div>
  )
}
