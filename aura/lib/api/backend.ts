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
}

export interface BackendChatResponse {
  answer: string
  sources: Array<
    | string
    | {
        file?: string
        url?: string
        title?: string
        cluster?: string
        /** BE-1 */
        start_line?: number
        end_line?: number
        /** BE-2 */
        document_year?: string
      }
  >
  is_personal_data?: boolean
}
