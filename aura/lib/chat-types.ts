/**
 * Structured data carried on the "calendar-action" SSE event. Two variants
 * share the channel, discriminated by `type`:
 *   - "booking" (default): a booking/reminder was created — Backend M3 (Dhruvam)
 *     owns that tool logic; rendered as a confirmation card.
 *   - "connect_required": the student asked for a calendar action but hasn't
 *     linked Google Calendar — rendered as an inline "Connect Google Calendar"
 *     CTA (the GPT/Claude connector pattern). Set by the orchestrator when a
 *     calendar tool returns calendar_not_connected.
 *   - "timetable_sync": a background timetable sync was accepted — rendered
 *     as a progress card while the frontend polls the app's calendar facade.
 *   - "timetable_sync_confirmation": a preview is ready for explicit user
 *     confirmation before any calendar events are written.
 *   - "confirmation_required": the backend is asking the student to confirm a
 *     calendar write (sync preview or unsync). Rendered as inline Confirm /
 *     Cancel buttons; Confirm sends "confirm" through the normal chat path so
 *     the backend confirmation gate is unchanged.
 */
export interface CalendarActionData {
  type?:
    | "booking"
    | "connect_required"
    | "timetable_sync"
    | "timetable_sync_confirmation"
    | "confirmation_required"
  event_title?: string
  date?: string
  time?: string
  attendees?: string[]
  status?: "confirmed" | "pending" | "failed"
  calendar_link?: string
  description?: string
  // connect_required variant
  provider?: string
  connect_path?: string
  reason?: string
  message?: string
  event_count?: number
  // confirmation_required variant: which calendar write awaits the go-ahead.
  action?: "sync_timetable" | "unsync_timetable"
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  timestamp?: number
  is_personal_data?: boolean
  /** Set when the backend emits a calendar-action SSE event for this turn. */
  calendar_action?: CalendarActionData
  /** Sources returned by the backend for this turn (assistant messages only). Persisted per-message so citations survive thread switches and reloads. */
  citations?: Citation[]
}

export interface Citation {
  file: string
  title?: string
  visibility?: string
  authorization?: string[]
  /** Relative path to the raw markdown source (e.g. "infrastructure/foo.md"), used to open the citation side-drawer. Absent for citations that are external URLs only. */
  path?: string
  startLine?: number
  endLine?: number
}

export interface ChatThread {
  id: string
  title: string
  /** Epoch ms of the most recent message; used to group threads by recency in the sidebar. */
  updatedAt?: number
  /** Rolling conversation memory: a digest of the turns older than `summaryTurnCount`, maintained by the backend (pipeline.memory) and persisted here so a long chat keeps its context. */
  summary?: string
  /** Count of leading messages already folded into `summary`. The client sends only `messages.slice(summaryTurnCount)` (plus `summary`) to the backend. */
  summaryTurnCount?: number
  /** Set when this thread was auto-created as the continuation of another on hard context overflow; drives the "Continued from previous conversation" divider. */
  continuedFromId?: string
}

export interface StudentProfile {
  name: string
  program: string
  year: string
  interests: string
}

export interface UserSession {
  name: string
  email: string
  role?: "student" | "faculty" | "admin" | "faculty_coord" | "faculty_convenor_ug" | "faculty_convenor_pg" | "dean_students" | "dean_faculty" | "dean_academic" | "registrar" | "admin_staff" | "superadmin"
  department?: string
}
