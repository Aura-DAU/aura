"use client"

import React from "react"
import { Calendar, BookOpen, Clock, AlertTriangle, CreditCard, ArrowRight } from "lucide-react"

interface StudentDashboardProps {
  userName: string
  departmentName?: string
  onSelectPrompt: (text: string) => void
}

export function StudentDashboard({ userName, departmentName = "Information & Communication Technology", onSelectPrompt }: StudentDashboardProps) {
  const timetable = [
    { time: "09:00 AM - 10:30 AM", course: "Computer Networks (IT-302)", room: "Lab 3, Phase 1" },
    { time: "11:00 AM - 12:30 PM", course: "Software Engineering (IT-304)", room: "Room 102" },
    { time: "02:00 PM - 03:30 PM", course: "Technical Writing (HS-201)", room: "Room 110" },
  ]

  const attendance = [
    { course: "Computer Networks", attendance: 82 },
    { course: "Software Engineering", attendance: 71 },
    { course: "Technical Writing", attendance: 95 },
  ]

  const quickPrompts = [
    "What is my attendance status?",
    "When is the next exam?",
    "Show my fee structure",
    "Where is Room 102?",
  ]

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 text-left animate-in fade-in slide-in-from-bottom-3 duration-200">
      {/* Welcome banner */}
      <div className="mb-6 rounded-2xl border border-theme-gray-light bg-theme-gray/40 p-6 backdrop-blur-md">
        <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-bold text-transparent md:text-2xl">
          Welcome back, {userName}!
        </h1>
        <p className="mt-1 text-xs text-neutral-400">
          Student · {departmentName}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Timetable */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
          <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            <Calendar className="size-3.5 text-theme-yellow" />
            Today&apos;s Classes
          </h2>
          <div className="space-y-3">
            {timetable.map((item, idx) => (
              <div key={idx} className="flex flex-col gap-1 rounded-xl bg-theme-gray-light/40 p-3 border border-transparent hover:border-theme-gray-light transition-colors">
                <span className="flex items-center gap-1 text-[10px] text-neutral-400">
                  <Clock className="size-3" />
                  {item.time}
                </span>
                <span className="text-sm font-medium text-neutral-200">{item.course}</span>
                <span className="text-xs text-neutral-500">{item.room}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Attendance & Dues */}
        <div className="flex flex-col gap-5">
          <div className="flex-1 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <BookOpen className="size-3.5 text-theme-yellow" />
              Attendance Status
            </h2>
            <div className="space-y-2.5">
              {attendance.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between rounded-xl bg-theme-gray-light/40 px-3 py-2">
                  <span className="text-xs font-medium text-neutral-300">{item.course}</span>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs font-semibold ${item.attendance < 75 ? "text-theme-red" : "text-neutral-400"}`}>
                      {item.attendance}%
                    </span>
                    {item.attendance < 75 && (
                      <span className="inline-flex items-center gap-1 rounded bg-theme-red/10 px-1.5 py-0.5 text-[9px] font-medium text-theme-red border border-theme-red/20 animate-pulse">
                        <AlertTriangle className="size-2.5" />
                        Low
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <CreditCard className="size-3.5 text-theme-yellow" />
              Fee Dues
            </h2>
            <div className="flex items-center justify-between rounded-xl bg-theme-gray-light/40 px-4 py-2">
              <span className="text-xs text-neutral-300">Semester Balance</span>
              <span className="text-xs font-semibold text-green-400 border border-green-500/20 bg-green-500/10 px-2 py-0.5 rounded-full">Paid ✅</span>
            </div>
          </div>
        </div>
      </div>

      {/* Starter prompts */}
      <div className="mt-8">
        <h3 className="mb-3 text-[10px] font-semibold uppercase tracking-wider text-neutral-500">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2">
          {quickPrompts.map((prompt) => (
            <button
              key={prompt}
              type="button"
              onClick={() => onSelectPrompt(prompt)}
              className="flex items-center justify-between rounded-xl border border-theme-gray-light bg-theme-gray/60 px-4 py-2.5 text-left text-xs text-neutral-300 hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100 transition-all group"
            >
              <span>{prompt}</span>
              <ArrowRight className="size-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-theme-yellow" />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}