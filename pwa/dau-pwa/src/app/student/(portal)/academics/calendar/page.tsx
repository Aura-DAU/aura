"use client";

import React, { useState } from "react";

interface CalendarEvent {
  date: string;
  title: string;
  type: "academic" | "exam" | "holiday" | "event";
  desc: string;
  categoryBadge: string;
  badgeStyle: string;
}

const CALENDAR_EVENTS: CalendarEvent[] = [
  {
    date: "Jan 05, 2026",
    title: "Commencement of Winter Semester Classes",
    type: "academic",
    desc: "Academic registrations close and regular class sessions and lab cycles commence for all programs.",
    categoryBadge: "Semester Start",
    badgeStyle: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  },
  {
    date: "Jan 26, 2026",
    title: "Republic Day",
    type: "holiday",
    desc: "National Holiday. Administrative services and classrooms remain closed.",
    categoryBadge: "Holiday",
    badgeStyle: "bg-red-500/10 text-red-400 border border-red-500/20",
  },
  {
    date: "Feb 09 - Feb 12, 2026",
    title: "First In-Semester Examinations",
    type: "exam",
    desc: "First review examinations covering initial syllabus units. Normal classes suspended.",
    categoryBadge: "In-Sem I",
    badgeStyle: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  },
  {
    date: "Mar 02 - Mar 06, 2026",
    title: "Mid-Semester Recess",
    type: "holiday",
    desc: "Recess week for students. Laboratory sessions and lecture duties remain suspended.",
    categoryBadge: "Break",
    badgeStyle: "bg-purple-500/10 text-purple-400 border border-purple-500/20",
  },
  {
    date: "Mar 18 - Mar 23, 2026",
    title: "Second In-Semester Examinations",
    type: "exam",
    desc: "Second review examinations for all undergraduate and graduate student groups.",
    categoryBadge: "In-Sem II",
    badgeStyle: "bg-amber-500/10 text-amber-400 border border-amber-500/20",
  },
  {
    date: "Apr 29, 2026",
    title: "Last Date of Classes & Lab Submissions",
    type: "academic",
    desc: "Official conclusion of lecture syllabus and evaluation criteria submissions for the winter semester.",
    categoryBadge: "Classes End",
    badgeStyle: "bg-blue-500/10 text-blue-400 border border-blue-500/20",
  },
  {
    date: "Apr 30 - May 08, 2026",
    title: "End-Semester Final Examinations",
    type: "exam",
    desc: "Comprehensive evaluation exams across all courses. Individual timetables published by DAC.",
    categoryBadge: "Final Exams",
    badgeStyle: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
  },
];

export default function CalendarPage() {
  const [filterType, setFilterType] = useState<"all" | "academic" | "exam" | "holiday">("all");

  const filteredEvents = CALENDAR_EVENTS.filter(
    (ev) => filterType === "all" || ev.type === filterType
  );

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="border-b border-border-dau pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Academic Calendar
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Stay aligned with registration schedules, exam windows, breaks, and university milestones.
          </p>
        </div>

        {/* Filters Select */}
        <div className="flex gap-1.5 overflow-x-auto pb-1">
          {(["all", "academic", "exam", "holiday"] as const).map((type) => (
            <button
              key={type}
              onClick={() => setFilterType(type)}
              className={`px-3 py-1.5 rounded-full text-[10px] font-bold tracking-wider uppercase whitespace-nowrap transition-all duration-200 ${
                filterType === type
                  ? "bg-primary-dau text-white shadow-md shadow-primary-dau/20"
                  : "bg-surface-elevated/40 text-text-muted hover:text-foreground hover:bg-surface-elevated/70"
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Timeline Layout */}
      <div className="relative border-l border-border-dau/60 ml-4 pl-6 sm:pl-8 py-2 space-y-8 max-w-3xl">
        {filteredEvents.map((event, idx) => (
          <div key={idx} className="relative group">
            {/* Dot marker on timeline line */}
            <span
              className={`absolute -left-[31px] sm:-left-[39px] top-1.5 w-4.5 h-4.5 rounded-full border-4 border-background transition-all duration-300 group-hover:scale-110 ${
                event.type === "academic"
                  ? "bg-blue-500"
                  : event.type === "exam"
                  ? "bg-amber-500"
                  : event.type === "holiday"
                  ? "bg-red-500"
                  : "bg-purple-500"
              }`}
            />

            {/* Event Content Card container */}
            <div className="bg-surface-dau/15 border border-border-dau/50 rounded-2xl p-5 hover:bg-surface-elevated/30 hover:border-primary-dau/30 transition-all duration-200 shadow-lg shadow-background/20">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-3">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded text-[9px] font-bold tracking-wider uppercase ${event.badgeStyle}`}>
                    {event.categoryBadge}
                  </span>
                  <span className="text-[10px] text-text-muted font-bold font-mono">
                    {event.date}
                  </span>
                </div>
              </div>
              <h3 className="text-xs sm:text-sm font-extrabold text-foreground mb-1.5 group-hover:text-primary-dau transition-colors duration-150">
                {event.title}
              </h3>
              <p className="text-xs text-text-muted leading-relaxed">
                {event.desc}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
