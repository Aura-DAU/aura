"use client"

import React from "react"
import { useRouter } from "next/navigation"
import { StudentDashboard } from "@/components/features/chat-ui/StudentDashboard"
import { FacultyDashboard } from "@/components/features/chat-ui/FacultyDashboard"
import { InstallPromptBanner } from "@/components/features/chat-ui/InstallPromptBanner"
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

  let body: React.ReactNode

  if (role === "student") {
    body = (
      <StudentDashboard
        userName={userName}
        departmentName={departmentName}
        currentYear={user.currentYear}
        currentSem={user.currentSem}
        currentSec={user.currentSec}
        onSelectPrompt={handleSelectPrompt}
      />
    )
  } else if (role.startsWith("faculty") || role.startsWith("dean") || role === "registrar") {
    body = (
      <FacultyDashboard
        userName={userName}
        departmentName={departmentName}
        onSelectPrompt={handleSelectPrompt}
      />
    )
  } else if (role === "admin") {
    body = <AdminBindingsClient />
  } else {
    body = (
      <div className="flex h-screen items-center justify-center bg-theme-black text-neutral-100 font-sans">
        <p className="text-sm text-neutral-400">Unauthorized role access: {role}</p>
      </div>
    )
  }

  return (
    <>
      {body}
      <InstallPromptBanner />
    </>
  )
}
