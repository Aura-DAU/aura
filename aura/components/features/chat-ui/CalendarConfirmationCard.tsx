"use client"

import { useEffect, useRef, useState } from "react"
import { CalendarCheck, CalendarX2, Check, Loader2 } from "lucide-react"
import { cn } from "@/lib/utils"
import type { CalendarActionData } from "@/lib/chat-types"

interface CalendarConfirmationCardProps {
  action: CalendarActionData
  /**
   * Sends "confirm" through the normal chat send path (the backend keys the
   * write off that message). Absent when this turn can no longer be confirmed
   * (an older message, or a reply is already streaming).
   */
  onConfirm?: () => void
}

type ConfirmationState = "idle" | "confirming" | "confirmed" | "cancelled"

// Inline confirm-before-write buttons for calendar actions — the GPT/Claude
// tool-use confirmation pattern, mirroring ConnectCalendarCard. Confirming
// dispatches a regular "confirm" chat message so the backend confirmation
// gate stays the single write authorizer; Cancel is purely client-side (the
// backend writes nothing unless it receives the confirmation).
export function CalendarConfirmationCard({
  action,
  onConfirm,
}: CalendarConfirmationCardProps) {
  const [state, setState] = useState<ConfirmationState>("idle")
  const settleTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    return () => {
      if (settleTimerRef.current) clearTimeout(settleTimerRef.current)
    }
  }, [])

  const isRemoval = action.action === "unsync_timetable"
  const expired = state === "idle" && !onConfirm

  const handleConfirm = () => {
    if (!onConfirm || state !== "idle") return
    setState("confirming")
    onConfirm()
    // Brief pressed/loading beat before settling into the success state; the
    // actual result arrives as the next assistant message.
    settleTimerRef.current = setTimeout(() => setState("confirmed"), 650)
  }

  const Icon = isRemoval ? CalendarX2 : CalendarCheck

  return (
    <div
      className={cn(
        "mt-3 rounded-xl border p-4 animate-in fade-in slide-in-from-bottom-1 duration-300",
        isRemoval
          ? "border-theme-red/20 bg-theme-red/5"
          : "border-theme-yellow/20 bg-theme-yellow/5",
      )}
    >
      <div className="flex items-start gap-2.5">
        <Icon
          className={cn(
            "mt-0.5 size-4 shrink-0",
            isRemoval ? "text-theme-red" : "text-theme-yellow",
          )}
        />
        <div className="min-w-0 flex-1">
          <p
            className={cn(
              "mb-1 text-xs font-semibold",
              isRemoval ? "text-theme-red" : "text-theme-yellow",
            )}
          >
            {isRemoval
              ? "Remove synced timetable events?"
              : "Sync timetable to Google Calendar?"}
          </p>
          <p className="text-sm text-neutral-300">
            {isRemoval
              ? "Every class event AURA added will be removed from your Google Calendar."
              : action.event_count
                ? `${action.event_count} recurring weekly class events will be created or updated.`
                : "Your recurring weekly class events will be created or updated."}
          </p>

          {state === "confirmed" ? (
            <p
              role="status"
              className="mt-3 inline-flex items-center gap-1.5 text-xs font-medium text-green-400 animate-in fade-in zoom-in-95 duration-300"
            >
              <Check className="size-3.5" />
              Confirmed — {isRemoval ? "clearing the events." : "syncing your timetable."}
            </p>
          ) : state === "cancelled" ? (
            <p role="status" className="mt-3 text-xs text-neutral-500 animate-in fade-in duration-300">
              Cancelled — nothing was changed.
            </p>
          ) : expired ? (
            <p className="mt-2 text-xs text-neutral-500">
              This confirmation is no longer pending.
            </p>
          ) : (
            <div className="mt-3 flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={handleConfirm}
                disabled={state === "confirming"}
                className={cn(
                  "inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2 text-sm font-bold text-black transition-all duration-150",
                  "hover:opacity-90 active:scale-[0.97]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/40",
                  state === "confirming" && "scale-[0.98] opacity-75",
                )}
              >
                {state === "confirming" ? (
                  <>
                    <Loader2 className="size-4 animate-spin" />
                    Confirming…
                  </>
                ) : (
                  <>
                    <Icon className="size-4" />
                    Confirm
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => setState("cancelled")}
                disabled={state === "confirming"}
                className={cn(
                  "inline-flex items-center rounded-xl border border-theme-gray-light px-4 py-2 text-sm font-medium text-neutral-300 transition-all duration-150",
                  "hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100 active:scale-[0.97]",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-theme-yellow/35",
                  "disabled:opacity-50",
                )}
              >
                Cancel
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
