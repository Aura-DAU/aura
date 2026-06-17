export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  timestamp?: number
}

export interface Citation {
  file: string
  title?: string
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
}
