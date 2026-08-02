import { BrandMark } from "@/components/ui/brand-mark"

interface StreamingIndicatorProps {
  thinkingStep?: string
}

export function StreamingIndicator({ thinkingStep }: StreamingIndicatorProps) {
  return (
    <div className="msg-enter flex items-start gap-3">
      <BrandMark className="mt-0.5 size-8" isActive />
      <div className="flex min-h-9 items-center gap-2.5 pt-1">
        <div className="flex items-center gap-1" aria-hidden="true">
          <span className="chat-v2-dot size-1.5 rounded-full bg-theme-red" style={{ animationDelay: "0ms" }} />
          <span className="chat-v2-dot size-1.5 rounded-full bg-theme-yellow" style={{ animationDelay: "150ms" }} />
          <span className="chat-v2-dot size-1.5 rounded-full bg-theme-red" style={{ animationDelay: "300ms" }} />
        </div>
        <span className="text-shimmer text-sm font-medium transition-opacity duration-300">
          {thinkingStep || "Thinking…"}
        </span>
        <span className="sr-only">AURA is responding</span>
      </div>
    </div>
  )
}

