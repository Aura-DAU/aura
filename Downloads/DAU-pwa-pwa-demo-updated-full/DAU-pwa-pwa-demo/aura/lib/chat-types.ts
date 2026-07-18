/**
 * Structured data returned by the backend calendar tool when a booking
 * or reminder is created. Populated only when chunk.type === "calendar-action"
 * arrives in the SSE stream. Backend M3 (Dhruvam) owns the tool logic.
 */
export interface CalendarActionData {
  event_title?: string
  date?: string
  time?: string
  attendees?: string[]
  status?: "confirmed" | "pending" | "failed"
  calendar_link?: string
  description?: string
}

export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  timestamp?: number
  is_personal_data?: boolean
  /** Set when the backend emits a calendar-action SSE event for this turn. */
  calendar_action?: CalendarActionData
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
