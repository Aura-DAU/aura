"use client"

import React from "react"
import { Calendar, Users, Clock, AlertCircle, ArrowRight } from "lucide-react"

interface FacultyDashboardProps {
  userName: string
  departmentName?: string
  onSelectPrompt: (text: string) => void
}

export function FacultyDashboard({ userName, departmentName = "Information & Communication Technology", onSelectPrompt }: FacultyDashboardProps) {
  const schedule = [
    { time: "10:00 AM - 11:30 AM", course: "Computer Networks (IT-302) - PG", room: "Room 201" },
    { time: "02:00 PM - 05:00 PM", course: "Database Management Lab (IT-204) - UG", room: "Lab 1" },
  ]

  const alerts = [
    { title: "Networks Lab Grade Sheet", due: "10th July (In 6 days)" },
  ]

  const quickPrompts = [
    "What is my class schedule today?",
    "Show pending grade submissions",
    "List my BTP mentee groups",
    "Check room availability for seminar",
  ]

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-8 text-left animate-in fade-in slide-in-from-bottom-3 duration-200">
      {/* Welcome banner */}
      <div className="mb-6 rounded-2xl border border-theme-gray-light bg-theme-gray/40 p-6 backdrop-blur-md">
        <h1 className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-xl font-bold text-transparent md:text-2xl">
          Welcome back, Prof. {userName}!
        </h1>
        <p className="mt-1 text-xs text-neutral-400">
          Faculty · {departmentName}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
        {/* Teaching schedule */}
        <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
          <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
            <Calendar className="size-3.5 text-theme-yellow" />
            Today&apos;s Schedule
          </h2>
          <div className="space-y-3">
            {schedule.map((item, idx) => (
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

        {/* Alerts & Mentees */}
        <div className="flex flex-col gap-5">
          <div className="flex-1 rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <AlertCircle className="size-3.5 text-theme-yellow" />
              Pending Tasks
            </h2>
            <div className="space-y-2.5">
              {alerts.map((item, idx) => (
                <div key={idx} className="flex flex-col gap-1 rounded-xl bg-theme-red/5 border border-theme-red/20 p-3">
                  <span className="text-xs font-medium text-neutral-200">{item.title}</span>
                  <span className="text-[10px] text-theme-red font-medium">Due: {item.due}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-5">
            <h2 className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-neutral-400">
              <Users className="size-3.5 text-theme-yellow" />
              Project Mentees (BTP)
            </h2>
            <div className="flex items-center justify-between rounded-xl bg-theme-gray-light/40 px-4 py-2">
              <span className="text-xs text-neutral-300">Supervised Groups</span>
              <span className="text-xs font-semibold text-theme-yellow bg-theme-yellow/10 border border-theme-yellow/20 px-2 py-0.5 rounded-full">4 Teams (12 studs)</span>
            </div>
          </div>
        </div>
      </div>

      {/* Suggested queries */}
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