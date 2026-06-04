"use client";

import React, { useState } from "react";

interface TimeSlot {
  time: string;
  monday?: { subject: string; room: string; type: "lecture" | "lab"; color: string };
  tuesday?: { subject: string; room: string; type: "lecture" | "lab"; color: string };
  wednesday?: { subject: string; room: string; type: "lecture" | "lab"; color: string };
  thursday?: { subject: string; room: string; type: "lecture" | "lab"; color: string };
  friday?: { subject: string; room: string; type: "lecture" | "lab"; color: string };
}

const TIMETABLE_DATA: Record<string, TimeSlot[]> = {
  "B.Tech (ICT) - Sem V - Sec A": [
    {
      time: "09:00 AM - 10:00 AM",
      monday: { subject: "CT303: Digital Comm.", room: "LT-1", type: "lecture", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
      wednesday: { subject: "CT303: Digital Comm.", room: "LT-1", type: "lecture", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
      friday: { subject: "CT303: Digital Comm.", room: "LT-1", type: "lecture", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
    },
    {
      time: "10:00 AM - 11:00 AM",
      tuesday: { subject: "IT314: Software Engg.", room: "LT-2", type: "lecture", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
      thursday: { subject: "IT314: Software Engg.", room: "LT-2", type: "lecture", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
    },
    {
      time: "11:00 AM - 12:00 PM",
      monday: { subject: "HM333: Org. Behavior", room: "LT-1", type: "lecture", color: "border-purple-500/30 bg-purple-500/5 text-purple-400" },
      wednesday: { subject: "HM333: Org. Behavior", room: "LT-1", type: "lecture", color: "border-purple-500/30 bg-purple-500/5 text-purple-400" },
      friday: { subject: "HM333: Org. Behavior", room: "LT-1", type: "lecture", color: "border-purple-500/30 bg-purple-500/5 text-purple-400" },
    },
    {
      time: "12:00 PM - 01:00 PM",
      tuesday: { subject: "EL311: DSP Hardware", room: "LT-3", type: "lecture", color: "border-amber-500/30 bg-amber-500/5 text-amber-400" },
      thursday: { subject: "EL311: DSP Hardware", room: "LT-3", type: "lecture", color: "border-amber-500/30 bg-amber-500/5 text-amber-400" },
    },
    {
      time: "01:00 PM - 02:00 PM",
      // Lunch break slot
    },
    {
      time: "02:00 PM - 04:00 PM",
      monday: { subject: "IT314: SE Lab (G1)", room: "Lab-3", type: "lab", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
      tuesday: { subject: "CT303: DC Lab (G2)", room: "Lab-1", type: "lab", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
      wednesday: { subject: "EL311: DSP Lab (G1)", room: "Lab-5", type: "lab", color: "border-amber-500/30 bg-amber-500/5 text-amber-400" },
      thursday: { subject: "IT314: SE Lab (G2)", room: "Lab-3", type: "lab", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
      friday: { subject: "CT303: DC Lab (G1)", room: "Lab-1", type: "lab", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
    },
  ],
  "B.Tech (ICT) - Sem V - Sec B": [
    {
      time: "09:00 AM - 10:00 AM",
      tuesday: { subject: "IT314: Software Engg.", room: "LT-2", type: "lecture", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
      thursday: { subject: "IT314: Software Engg.", room: "LT-2", type: "lecture", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
    },
    {
      time: "10:00 AM - 11:00 AM",
      monday: { subject: "CT303: Digital Comm.", room: "LT-1", type: "lecture", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
      wednesday: { subject: "CT303: Digital Comm.", room: "LT-1", type: "lecture", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
      friday: { subject: "CT303: Digital Comm.", room: "LT-1", type: "lecture", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
    },
    {
      time: "11:00 AM - 12:00 PM",
      tuesday: { subject: "EL311: DSP Hardware", room: "LT-3", type: "lecture", color: "border-amber-500/30 bg-amber-500/5 text-amber-400" },
      thursday: { subject: "EL311: DSP Hardware", room: "LT-3", type: "lecture", color: "border-amber-500/30 bg-amber-500/5 text-amber-400" },
    },
    {
      time: "12:00 PM - 01:00 PM",
      monday: { subject: "HM333: Org. Behavior", room: "LT-1", type: "lecture", color: "border-purple-500/30 bg-purple-500/5 text-purple-400" },
      wednesday: { subject: "HM333: Org. Behavior", room: "LT-1", type: "lecture", color: "border-purple-500/30 bg-purple-500/5 text-purple-400" },
      friday: { subject: "HM333: Org. Behavior", room: "LT-1", type: "lecture", color: "border-purple-500/30 bg-purple-500/5 text-purple-400" },
    },
    {
      time: "01:00 PM - 02:00 PM",
      // Lunch break
    },
    {
      time: "02:00 PM - 04:00 PM",
      monday: { subject: "CT303: DC Lab (G1)", room: "Lab-1", type: "lab", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
      tuesday: { subject: "IT314: SE Lab (G1)", room: "Lab-3", type: "lab", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
      wednesday: { subject: "CT303: DC Lab (G2)", room: "Lab-1", type: "lab", color: "border-blue-500/30 bg-blue-500/5 text-blue-400" },
      thursday: { subject: "EL311: DSP Lab (G2)", room: "Lab-5", type: "lab", color: "border-amber-500/30 bg-amber-500/5 text-amber-400" },
      friday: { subject: "IT314: SE Lab (G2)", room: "Lab-3", type: "lab", color: "border-emerald-500/30 bg-emerald-500/5 text-emerald-400" },
    },
  ],
};

export default function TimetablePage() {
  const [selectedSchedule, setSelectedSchedule] = useState("B.Tech (ICT) - Sem V - Sec A");
  const slots = TIMETABLE_DATA[selectedSchedule] || [];

  const days: ("monday" | "tuesday" | "wednesday" | "thursday" | "friday")[] = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Lecture & Lab Timetables
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Access daily class hours, lab locations, classroom structures, and slots color-coded by course.
          </p>
        </div>

        {/* Schedule Selector */}
        <select
          value={selectedSchedule}
          onChange={(e) => setSelectedSchedule(e.target.value)}
          className="bg-surface-dau border border-border-dau/60 rounded-xl px-4 py-2 text-xs text-foreground focus:outline-none focus:border-primary-dau focus:ring-1 focus:ring-primary-dau/30 transition-all duration-200"
        >
          {Object.keys(TIMETABLE_DATA).map((sched) => (
            <option key={sched} value={sched}>
              {sched}
            </option>
          ))}
        </select>
      </div>

      {/* Timetable Grid Card container */}
      <div className="bg-surface-dau/20 border border-border-dau rounded-2xl overflow-hidden shadow-xl shadow-background/50">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse min-w-[800px] table-fixed">
            <thead>
              <tr className="bg-surface-elevated/40 border-b border-border-dau">
                <th className="w-40 px-4 py-3.5 text-xs font-bold uppercase tracking-wider text-left text-foreground">Time Slot</th>
                <th className="px-4 py-3.5 text-xs font-bold uppercase tracking-wider text-center text-foreground">Monday</th>
                <th className="px-4 py-3.5 text-xs font-bold uppercase tracking-wider text-center text-foreground">Tuesday</th>
                <th className="px-4 py-3.5 text-xs font-bold uppercase tracking-wider text-center text-foreground">Wednesday</th>
                <th className="px-4 py-3.5 text-xs font-bold uppercase tracking-wider text-center text-foreground">Thursday</th>
                <th className="px-4 py-3.5 text-xs font-bold uppercase tracking-wider text-center text-foreground">Friday</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-dau/30 bg-surface-dau/5">
              {slots.map((slot, idx) => {
                const isLunchBreak = slot.time === "01:00 PM - 02:00 PM";

                return (
                  <tr key={idx} className="hover:bg-surface-elevated/10 transition-colors duration-150">
                    <td className="px-4 py-6 text-xs font-bold text-text-muted border-r border-border-dau/20">
                      {slot.time}
                    </td>
                    {isLunchBreak ? (
                      <td colSpan={5} className="px-4 py-4 text-center text-xs font-bold uppercase tracking-widest text-text-muted/40 bg-surface-elevated/5">
                        Lunch Break
                      </td>
                    ) : (
                      days.map((day) => {
                        const cell = slot[day];
                        return (
                          <td key={day} className="p-2 border-r border-border-dau/20">
                            {cell ? (
                              <div
                                className={`h-full rounded-xl border p-3 flex flex-col items-center justify-center text-center shadow-sm transition-all duration-200 hover:scale-[1.03] ${cell.color}`}
                              >
                                <span className="text-xs font-extrabold tracking-tight leading-tight mb-1">
                                  {cell.subject}
                                </span>
                                <div className="flex items-center gap-1.5 mt-0.5">
                                  <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-background/50 border border-current/10">
                                    {cell.room}
                                  </span>
                                  <span className="text-[9px] font-bold uppercase tracking-wider opacity-85">
                                    {cell.type}
                                  </span>
                                </div>
                              </div>
                            ) : (
                              <div className="h-full min-h-[60px] flex items-center justify-center text-[10px] text-text-muted/20 italic">
                                Free Slot
                              </div>
                            )}
                          </td>
                        );
                      })
                    )}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
