"use client"

import React from "react"
import { useRouter } from "next/navigation"
import { StudentDashboard } from "@/components/features/chat-ui/StudentDashboard"
import { FacultyDashboard } from "@/components/features/chat-ui/FacultyDashboard"
import AdminBindingsClient from "./admin-client"

interface DashboardShellProps {
  user: {
    role: "student" | "faculty" | "admin" | "guest"
    name?: string | null
    email?: string | null
    department?: string
    erpId: string
    currentYear?: number
    currentSem?: number
    currentSec?: string
  }
}

export default function DashboardShell({ user }: DashboardShellProps) {
  const router = useRouter()

  const handleSelectPrompt = (text: string) => {
    // Elegant redirect fallback: when clicking quick actions inside /dashboard,
    // it transfers the user to the main page and initiates the prompt in chat
    router.push(`/?prompt=${encodeURIComponent(text)}`)
  }

  const role = (user.role as string) || ""
  const userName = user.name || "User"
  const departmentName = user.department

  if (role === "student") {
    return (
      <StudentDashboard
        userName={userName}
        departmentName={departmentName}
        currentYear={user.currentYear}
        currentSem={user.currentSem}
        currentSec={user.currentSec}
        onSelectPrompt={handleSelectPrompt}
      />
    )
  }

  if (role.startsWith("faculty") || role.startsWith("dean") || role === "registrar") {
    return (
      <FacultyDashboard
        userName={userName}
        departmentName={departmentName}
        onSelectPrompt={handleSelectPrompt}
      />
    )
  }

  if (role === "admin") {
    return <AdminBindingsClient />
  }

  return (
    <div className="flex h-screen items-center justify-center bg-theme-black text-neutral-100 font-sans">
      <p className="text-sm text-neutral-400">Unauthorized role access: {role}</p>
    </div>
  )
}
