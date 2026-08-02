import type { CalendarActionData } from "@/lib/chat-types"

const BACKGROUND_CALENDAR_SYNC_RESPONSE =
  /^Sync started in the background(?: for (\d+) slots)?\.\s*Check status at GET \/calendar\/timetable\/sync\/status\.?$/i

const CALENDAR_SYNC_CONFIRMATION_RESPONSE =
  /^This will create or update (\d+) recurring weekly events on your Google Calendar\b[\s\S]*Confirm to proceed\.?$/i

export function toCalendarSyncAction(response: string): CalendarActionData | undefined {
  const normalized = response.trim()
  const queuedMatch = normalized.match(BACKGROUND_CALENDAR_SYNC_RESPONSE)
  if (queuedMatch) {
    return {
      type: "timetable_sync",
      status: "pending",
      event_count: queuedMatch[1] ? Number(queuedMatch[1]) : undefined,
    }
  }

  const confirmationMatch = normalized.match(CALENDAR_SYNC_CONFIRMATION_RESPONSE)
  if (!confirmationMatch) return undefined

  return {
    type: "timetable_sync_confirmation",
    status: "pending",
    event_count: Number(confirmationMatch[1]),
  }
}
