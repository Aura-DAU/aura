"use client"

import React from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { MessageSquare } from "lucide-react"
import { StudentDashboard } from "@/components/ui/student-dashboard"
import { FacultyDashboard } from "@/components/ui/faculty-dashboard"
import AdminBindingsClient from "./admin-client"
import { BrandMark } from "@/components/ui/brand-mark"

interface DashboardShellProps {
  user: {
    role: "student" | "faculty" | "admin" | "guest"
    name?: string | null
    email?: string | null
    department?: string
    erpId: string
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
      <div className="flex flex-1 items-center justify-center px-4 py-16">
        <p className="text-sm text-neutral-400">Unauthorized role access: {role}</p>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-theme-black text-neutral-100">
      <header className="sticky top-0 z-20 border-b border-theme-gray-light/60 bg-theme-black/70 backdrop-blur">
        <div className="mx-auto flex h-14 w-full max-w-3xl items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <BrandMark className="size-7 text-xs" />
            <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-sm font-semibold text-transparent">
              AURA
            </span>
            <span className="text-xs text-neutral-500">Dashboard</span>
          </div>
          <Link
            href="/"
            className="inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm text-neutral-300 transition-colors hover:bg-theme-gray-light hover:text-neutral-100"
          >
            <MessageSquare className="size-4 text-theme-yellow" />
            Back to chat
          </Link>
        </div>
      </header>
      {body}
    </div>
  )
}
