export interface ChatMessage {
  role: "user" | "assistant"
  content: string
  timestamp?: number
  is_personal_data?: boolean
}

export interface Citation {
  file: string
  title?: string
  visibility?: string
  authorization?: string[]
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
