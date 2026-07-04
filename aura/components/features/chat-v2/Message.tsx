"use client"

import { useState } from "react"
import { Check, Copy, RotateCcw, ThumbsDown, ThumbsUp, FileText, Lock } from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import type { ChatMessage, Citation } from "@/lib/chat-types"
import { BrandMark } from "@/components/common/BrandMark"
import { MarkdownContent } from "@/components/common/MarkdownContent"

interface MessageProps {
  message: ChatMessage
  citations?: Citation[]
  onRegenerate?: () => void
}

export function Message({ message, citations, onRegenerate }: MessageProps) {
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null)

    const getAuthBadge = (auth?: string[], visibility?: string) => {
    if (visibility) {
      const isFaculty = visibility.toLowerCase().includes("faculty")
      return (
        <span className={cn(
          "rounded-full px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider border",
          isFaculty 
            ? "bg-purple-500/10 text-purple-400 border-purple-500/20"
            : "bg-blue-500/10 text-blue-400 border-blue-500/20"
        )}>
          {visibility}
        </span>
      )
    }
    
    if (auth && auth.length > 0) {
      if (auth.includes("faculty")) {
        return (
          <span className="rounded-full bg-purple-500/10 px-2 py-0.5 text-[9px] font-semibold text-purple-400 border border-purple-500/20 uppercase tracking-wider">
            Faculty-only
          </span>
        )
      }
      if (auth.includes("student_ug") || auth.includes("ug")) {
        return (
          <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-[9px] font-semibold text-blue-400 border border-blue-500/20 uppercase tracking-wider">
            UG student
          </span>
        )
      }
      if (auth.includes("student_pg") || auth.includes("pg")) {
        return (
          <span className="rounded-full bg-teal-500/10 px-2 py-0.5 text-[9px] font-semibold text-teal-400 border border-teal-500/20 uppercase tracking-wider">
            PG student
          </span>
        )
      }
      return (
        <span className="rounded-full bg-neutral-500/10 px-2 py-0.5 text-[9px] font-semibold text-neutral-400 border border-neutral-500/20 uppercase tracking-wider">
          {auth[0]}
        </span>
      )
    }
    return null
  }
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[75%] rounded-2xl bg-theme-gray-light px-4 py-2.5 text-sm leading-relaxed text-neutral-100">
          {message.content}
        </div>
      </div>
    )
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      toast.error("Could not copy message")
    }
  }

  const handleFeedback = (value: "up" | "down") => {
    setFeedback((prev) => (prev === value ? null : value))
    toast.success("Thanks for the feedback")
  }

  return (
    <div className="group flex items-start gap-3">
      <BrandMark className="mt-0.5 size-8 text-sm" />
      <div className="min-w-0 flex-1">
        {message.is_personal_data && (
          <div className="mb-2 inline-flex items-center gap-1.5 rounded-lg border border-theme-yellow/20 bg-theme-yellow/10 px-2.5 py-1 text-xs text-theme-yellow font-medium select-none">
            <Lock className="size-3 text-theme-yellow" />
            <span>Your personal data</span>
          </div>
        )}
        <MarkdownContent content={message.content} />

        {citations && citations.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-3">
            {citations.map((c, i) => {
              const isUrl = c.file.startsWith("http://") || c.file.startsWith("https://")
              const Component = isUrl ? "a" : "span"
              const badge = getAuthBadge(c.authorization, c.visibility)
              return (
                <div key={`${c.file}-${i}`} className="inline-flex items-center gap-1.5">
                  <Component
                    href={isUrl ? c.file : undefined}
                    target={isUrl ? "_blank" : undefined}
                    rel={isUrl ? "noopener noreferrer" : undefined}
                    className={cn(
                      "inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray px-2.5 py-1 text-xs text-neutral-300",
                      isUrl && "hover:bg-theme-gray-light transition-colors cursor-pointer hover:text-neutral-100"
                    )}
                  >
                    <span className="size-1.5 rounded-full bg-theme-yellow" />
                    <FileText className="size-3 text-neutral-500" />
                    {c.title ?? c.file}
                  </Component>
                  {badge}
                </div>
              )
            })}
          </div>
        ) : null}

        <div className="mt-2 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <ActionButton label={copied ? "Copied" : "Copy"} onClick={handleCopy}>
            {copied ? (
              <Check className="size-4 text-theme-yellow" />
            ) : (
              <Copy className="size-4" />
            )}
          </ActionButton>
          {onRegenerate ? (
            <ActionButton label="Regenerate" onClick={onRegenerate}>
              <RotateCcw className="size-4" />
            </ActionButton>
          ) : null}
          <ActionButton
            label="Good response"
            onClick={() => handleFeedback("up")}
            active={feedback === "up"}
          >
            <ThumbsUp className="size-4" />
          </ActionButton>
          <ActionButton
            label="Bad response"
            onClick={() => handleFeedback("down")}
            active={feedback === "down"}
          >
            <ThumbsDown className="size-4" />
          </ActionButton>
        </div>
      </div>
    </div>
  )
}

interface ActionButtonProps {
  label: string
  onClick: () => void
  active?: boolean
  children: React.ReactNode
}

function ActionButton({ label, onClick, active, children }: ActionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      className={cn(
        "rounded-lg p-1.5 text-neutral-500 transition-colors hover:bg-theme-gray-light hover:text-neutral-200",
        active && "text-theme-yellow",
      )}
    >
      {children}
    </button>
  )
}
