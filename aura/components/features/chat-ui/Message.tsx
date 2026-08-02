"use client"

import { useEffect, useRef, useState } from "react"
import {
  Check,
  Copy,
  RotateCcw,
  ThumbsDown,
  ThumbsUp,
  FileText,
  Lock,
  CalendarCheck,
} from "lucide-react"
import { toast } from "sonner"
import { cn } from "@/lib/utils"
import type { ChatMessage, Citation, CalendarActionData } from "@/lib/chat-types"
import { BrandMark } from "@/components/ui/brand-mark"
import { MarkdownContent } from "@/components/ui/markdown-content"
import { useDocumentViewer } from "@/hooks/use-document-viewer"
import { useGoogleCalendarSync } from "@/hooks/use-google-calendar-sync"
import { TimetableSyncCard } from "./TimetableSyncCard"
import { TimetableSyncConfirmationCard } from "./TimetableSyncConfirmationCard"

interface MessageProps {
  message: ChatMessage
  citations?: Citation[]
  onRegenerate?: () => void
  /** While streaming, render plain text to avoid re-parsing Markdown every token. */
  isStreaming?: boolean
  /** Keep action toolbar visible (ChatGPT pattern for the latest reply). */
  showActions?: boolean
  onCalendarSyncConfirm?: () => void
}

export function Message({
  message,
  citations,
  onRegenerate,
  isStreaming = false,
  showActions = false,
  onCalendarSyncConfirm,
}: MessageProps) {
  const [copied, setCopied] = useState(false)
  const [feedback, setFeedback] = useState<"up" | "down" | null>(null)
  const copyTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { openDocument, prefetchDocument } = useDocumentViewer()

  useEffect(() => {
    return () => {
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current)
      if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
    }
  }, [])

  const getAuthBadge = (auth?: string[], visibility?: string) => {
    if (visibility) {
      const isFaculty = visibility.toLowerCase().includes("faculty")
      return (
        <span
          className={cn(
            "rounded-full border px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider",
            isFaculty
              ? "border-purple-500/20 bg-purple-500/10 text-purple-400"
              : "border-blue-500/20 bg-blue-500/10 text-blue-400",
          )}
        >
          {visibility}
        </span>
      )
    }

    if (auth && auth.length > 0) {
      if (auth.includes("faculty")) {
        return (
          <span className="rounded-full border border-purple-500/20 bg-purple-500/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-purple-400">
            Faculty-only
          </span>
        )
      }
      if (auth.includes("student_ug") || auth.includes("ug")) {
        return (
          <span className="rounded-full border border-blue-500/20 bg-blue-500/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-blue-400">
            UG student
          </span>
        )
      }
      if (auth.includes("student_pg") || auth.includes("pg")) {
        return (
          <span className="rounded-full border border-teal-500/20 bg-teal-500/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-teal-400">
            PG student
          </span>
        )
      }
      return (
        <span className="rounded-full border border-neutral-500/20 bg-neutral-500/10 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-wider text-neutral-400">
          {auth[0]}
        </span>
      )
    }
    return null
  }

  if (message.role === "user") {
    return (
      <div className="msg-enter flex justify-end">
        <div className="max-w-[min(75%,42rem)] 2xl:max-w-[min(75%,56rem)] rounded-[22px] rounded-br-lg bg-theme-gray-light px-4 py-2.5 text-[15px] leading-relaxed text-neutral-100 shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]">
          {message.content}
        </div>
      </div>
    )
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content)
      setCopied(true)
      if (copyTimerRef.current) clearTimeout(copyTimerRef.current)
      copyTimerRef.current = setTimeout(() => setCopied(false), 1600)
    } catch {
      toast.error("Could not copy message")
    }
  }

  const handleFeedback = (value: "up" | "down") => {
    setFeedback((prev) => (prev === value ? null : value))
    toast.success("Thanks for the feedback")
  }

  const looksLikeSoftFailure =
    /i'?m having trouble (retrieving information|reaching the student records)/i.test(
      message.content,
    ) || /sorry, i encountered an error while processing/i.test(message.content)

  return (
    <div className="msg-enter group flex items-start gap-3">
      <BrandMark className="mt-0.5 size-8 transition-transform duration-300 group-hover:scale-[1.03]" isActive={isStreaming} />
      <div className="min-w-0 flex-1">
        {message.is_personal_data && (
          <div className="mb-2 inline-flex items-center gap-1.5 rounded-lg border border-theme-yellow/20 bg-theme-yellow/10 px-2.5 py-1 text-xs font-medium text-theme-yellow select-none">
            <Lock className="size-3 text-theme-yellow" />
            <span>Your personal data</span>
          </div>
        )}

        {message.calendar_action?.type === "timetable_sync" ||
        message.calendar_action?.type === "timetable_sync_confirmation" ? null : isStreaming ? (
          <div className="whitespace-pre-wrap text-[15px] leading-[1.7] text-neutral-100">
            {message.content}
            <span className="msg-caret ml-0.5 inline-block align-text-bottom" />
          </div>
        ) : message.content.trim() ? (
          <div
            className={cn(
              "text-[15px] leading-[1.7]",
              looksLikeSoftFailure && "text-neutral-300",
            )}
          >
            <MarkdownContent content={message.content} citations={citations} />
          </div>
        ) : (
          <p className="text-[15px] leading-[1.7] text-neutral-500">
            No response generated.
          </p>
        )}

        {!isStreaming && looksLikeSoftFailure && onRegenerate ? (
          <p className="mt-2 text-xs text-neutral-500">
            Something went wrong retrieving that answer.{" "}
            <button
              type="button"
              onClick={onRegenerate}
              className="font-medium text-theme-yellow underline-offset-2 transition-colors hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/35"
            >
              Try regenerating
            </button>
          </p>
        ) : null}

        {message.calendar_action &&
          (message.calendar_action.type === "timetable_sync" ? (
            <TimetableSyncCard eventCount={message.calendar_action.event_count} />
          ) : message.calendar_action.type === "timetable_sync_confirmation" ? (
            <TimetableSyncConfirmationCard
              eventCount={message.calendar_action.event_count}
              onConfirm={onCalendarSyncConfirm}
            />
          ) : message.calendar_action.type === "connect_required" ? (
            <ConnectCalendarCard action={message.calendar_action} />
          ) : (
            <BookingConfirmationCard action={message.calendar_action} />
          ))}

        {citations && citations.length > 0 ? (
          <div className="mt-3 flex flex-wrap gap-2">
            {citations.map((c, i) => {
              const isUrl = c.file.startsWith("http://") || c.file.startsWith("https://")
              const hasSource = Boolean(c.path)
              const badge = getAuthBadge(c.authorization, c.visibility)
              const pillClasses = cn(
                "inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray/80 px-2.5 py-1 text-xs text-neutral-300 transition-all duration-150",
                (isUrl || hasSource) &&
                  "cursor-pointer hover:-translate-y-px hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100",
              )
              const label = (
                <>
                  <span className="size-1.5 rounded-full bg-theme-yellow" />
                  <FileText className="size-3 text-neutral-500" />
                  {c.title ?? c.file}
                </>
              )
              const viewerTarget = hasSource
                ? {
                    path: c.path!,
                    title: c.title ?? c.file,
                    startLine: c.startLine,
                    endLine: c.endLine,
                  }
                : null

              return (
                <div key={`${c.file}-${i}`} className="inline-flex items-center gap-1.5">
                  {/* Prefer the document viewer when a source path exists */}
                  {viewerTarget ? (
                    <button
                      type="button"
                      onMouseEnter={() => {
                        if (typeof window !== 'undefined' && window.innerWidth < 768) return;
                        prefetchDocument(viewerTarget)
                        if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
                        hoverTimerRef.current = setTimeout(() => {
                          openDocument(viewerTarget)
                        }, 1000)
                      }}
                      onMouseLeave={() => {
                        if (hoverTimerRef.current) clearTimeout(hoverTimerRef.current)
                      }}
                      onClick={() => {
                        window.open(c.file, "_blank", "noopener,noreferrer")
                      }}
                      className={pillClasses}
                      aria-label={`View source: ${c.title ?? c.file}`}
                    >
                      {label}
                    </button>
                  ) : isUrl ? (
                    <a href={c.file} target="_blank" rel="noopener noreferrer" className={pillClasses}>
                      {label}
                    </a>
                  ) : (
                    <span className={pillClasses}>{label}</span>
                  )}
                  {badge}
                </div>
              )
            })}
          </div>
        ) : null}

        {/* ChatGPT / Claude style action toolbar */}
        {!isStreaming ? (
          <div
            className={cn(
              "msg-actions mt-1.5 flex items-center gap-0.5",
              showActions
                ? "opacity-100"
                : "opacity-100 md:opacity-0 md:translate-y-0.5 md:group-hover:translate-y-0 md:group-hover:opacity-100 md:focus-within:translate-y-0 md:focus-within:opacity-100",
            )}
          >
            <div className="flex items-center gap-0.5">
              <ActionButton label={copied ? "Copied" : "Copy"} onClick={handleCopy} pressed={copied}>
                {copied ? (
                  <Check className="size-3.5 text-theme-yellow" />
                ) : (
                  <Copy className="size-3.5" />
                )}
              </ActionButton>
              {onRegenerate ? (
                <ActionButton label="Regenerate" onClick={onRegenerate}>
                  <RotateCcw className="size-3.5" />
                </ActionButton>
              ) : null}
            </div>

            <span className="mx-1.5 h-3 w-px bg-theme-gray-light" aria-hidden="true" />

            <div className="flex items-center gap-0.5">
              <ActionButton
                label="Good response"
                onClick={() => handleFeedback("up")}
                pressed={feedback === "up"}
              >
                <ThumbsUp className="size-3.5" />
              </ActionButton>
              <ActionButton
                label="Bad response"
                onClick={() => handleFeedback("down")}
                pressed={feedback === "down"}
              >
                <ThumbsDown className="size-3.5" />
              </ActionButton>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  )
}

interface ActionButtonProps {
  label: string
  onClick: () => void
  pressed?: boolean
  children: React.ReactNode
}

function ActionButton({ label, onClick, pressed, children }: ActionButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex size-8 items-center justify-center rounded-lg text-neutral-500 transition-all duration-150",
        "hover:bg-theme-gray-light hover:text-neutral-200",
        "active:scale-90",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/35",
        pressed && "bg-theme-gray-light text-theme-yellow",
      )}
    >
      <span className={cn("inline-flex transition-transform duration-200", pressed && "scale-110")}>
        {children}
      </span>
    </button>
  )
}

function BookingConfirmationCard({ action }: { action: CalendarActionData }) {
  const isConfirmed = action.status === "confirmed"
  const isFailed = action.status === "failed"

  return (
    <div
      className={cn(
        "mt-3 rounded-xl border p-4 animate-in fade-in slide-in-from-bottom-1 duration-300",
        isFailed
          ? "border-theme-red/20 bg-theme-red/5"
          : "border-theme-yellow/20 bg-theme-yellow/5",
      )}
    >
      <div className="flex items-start gap-2.5">
        <CalendarCheck
          className={cn(
            "mt-0.5 size-4 shrink-0",
            isFailed ? "text-theme-red" : "text-theme-yellow",
          )}
        />
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              "mb-1 text-xs font-semibold",
              isFailed ? "text-theme-red" : "text-theme-yellow",
            )}
          >
            {isFailed
              ? "Calendar event could not be created"
              : isConfirmed
                ? "Calendar event confirmed"
                : "Calendar event pending"}
          </p>
          {action.event_title && (
            <p className="text-sm font-medium text-neutral-200">{action.event_title}</p>
          )}
          {action.description && (
            <p className="mt-0.5 text-xs text-neutral-400">{action.description}</p>
          )}
          {(action.date || action.time) && (
            <p className="mt-1 flex items-center gap-1.5 text-xs text-neutral-400">
              <CalendarCheck className="size-3 shrink-0" />
              {[action.date, action.time].filter(Boolean).join(" · ")}
            </p>
          )}
          {action.attendees && action.attendees.length > 0 && (
            <p className="mt-1 text-xs text-neutral-500">
              With: {action.attendees.join(", ")}
            </p>
          )}
          {action.calendar_link && (
            <a
              href={action.calendar_link}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1 text-xs text-theme-yellow transition-colors hover:underline"
            >
              View in Google Calendar →
            </a>
          )}
        </div>
      </div>
    </div>
  )
}

// Inline "Connect Google Calendar" CTA — the GPT/Claude connector pattern.
// Rendered when a calendar tool reports the student hasn't linked their calendar
// yet. Reuses useGoogleCalendarSync so the button starts the same OAuth flow as
// Settings, and the card resolves to a "connected" state (no stale CTA on an old
// turn) once the account is linked.
function ConnectCalendarCard({ action }: { action: CalendarActionData }) {
  const { status, error, connect } = useGoogleCalendarSync()
  const connected = status === "connected"

  return (
    <div className="mt-3 rounded-xl border border-theme-yellow/20 bg-theme-yellow/5 p-4 animate-in fade-in slide-in-from-bottom-1 duration-300">
      <div className="flex items-start gap-2.5">
        <CalendarCheck className="mt-0.5 size-4 shrink-0 text-theme-yellow" />
        <div className="min-w-0 flex-1">
          <p className="mb-1 text-xs font-semibold text-theme-yellow">
            {connected ? "Google Calendar connected" : "Connect Google Calendar"}
          </p>
          <p className="text-sm text-neutral-300">
            {action.message ??
              "Connect your Google Calendar to add your timetable to your schedule."}
          </p>
          {error && <p className="mt-1.5 text-xs text-theme-red">{error}</p>}
          {connected ? (
            <p className="mt-2 inline-flex items-center gap-1 text-xs text-green-400">
              <Check className="size-3.5" /> Connected — ask me again to sync your timetable.
            </p>
          ) : (
            <button
              type="button"
              onClick={() => void connect()}
              disabled={status === "loading"}
              className="mt-3 inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2 text-sm font-bold text-black transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              <CalendarCheck className="size-4" />
              Connect Google Calendar
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
