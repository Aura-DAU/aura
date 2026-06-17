"use client";

import { useEffect, useRef } from "react";
import { ChatMessage, Citation } from "@/app/api/chat.service";
import Message from "./Message";
import StreamingIndicator from "./StreamingIndicator";

interface MessageListProps {
  messages: ChatMessage[];
  loading: boolean;
  thinkingStep?: string;
  citations: Citation[];
  onRegenerate?: () => void;
}

export default function MessageList({
  messages,
  loading,
  thinkingStep,
  citations,
  onRegenerate,
}: MessageListProps) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading, thinkingStep]);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-6 px-4 py-6">
      {messages.map((m, i) => {
        const isLastAssistant =
          m.role === "assistant" && i === messages.length - 1;
        return (
          <Message
            key={`${m.timestamp ?? i}-${m.role}`}
            message={m}
            citations={isLastAssistant ? citations : undefined}
            onRegenerate={isLastAssistant ? onRegenerate : undefined}
            isLast={isLastAssistant}
          />
        );
      })}
      {loading && <StreamingIndicator step={thinkingStep} />}
      <div ref={endRef} />
    </div>
  );
}
