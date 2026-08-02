export function backendUrl(path: string): string {
  const base = process.env.BACKEND_URL?.replace(/\/$/, "") ?? "http://localhost:8000"
  return `${base}${path.startsWith("/") ? path : `/${path}`}`
}

export interface BackendHistoryTurn {
  role: "user" | "assistant"
  content: string
}

export interface BackendStudentProfile {
  name?: string
  branch?: string
  year?: string
  semester?: string
  interests?: string
}

export interface BackendChatRequest {
  question: string
  history?: BackendHistoryTurn[]
  studentProfile?: BackendStudentProfile
  /** Client-owned rolling conversation memory (see lib/chat-types ChatThread.summary). */
  summary?: string
  /** Stable per-conversation id; keys this chat's block in the persistent per-user memory. */
  threadId?: string
}

export interface BackendChatResponse {
  answer: string
  sources: Array<
    | string
    | {
      file?: string
      url?: string
      title?: string
      path?: string
      start_line?: number | string | null
      end_line?: number | string | null
      visibility?: string
      authorization?: string[]
    }
  >
  is_personal_data?: boolean
  // Server's authoritative remaining-quota count for this identity (null for
  // unlimited @dau.ac.in roles). See server/api/routes/chat_routes.py.
  quota_remaining?: number | null
}
