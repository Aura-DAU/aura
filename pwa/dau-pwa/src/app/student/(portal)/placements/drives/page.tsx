"use client";

import React, { useState } from "react";

export default function UpcomingDrivesPage() {
  const [drives, setDrives] = useState([
    {
      company: "Google India",
      role: "Software Engineering Intern / Full Time",
      package: "₹32.5 - ₹48.0 LPA",
      eligibility: "B.Tech (ICT/CS/MnC), M.Tech (ICT) - Batch of 2026",
      status: "Open",
      deadline: "2026-06-15",
      logoBg: "bg-red-50 text-red-600 border-red-200",
      registered: false,
    },
    {
      company: "Microsoft",
      role: "Support Engineer / SWE Associate",
      package: "₹28.0 - ₹34.0 LPA",
      eligibility: "B.Tech (All Branches) - Batch of 2026",
      status: "Open",
      deadline: "2026-06-18",
      logoBg: "bg-blue-50 text-blue-600 border-blue-200",
      registered: false,
    },
    {
      company: "Sprinklr",
      role: "Product Engineer",
      package: "₹30.0 LPA",
      eligibility: "B.Tech (ICT/CS/MnC) - Min 7.5 CPI",
      status: "Open",
      deadline: "2026-06-20",
      logoBg: "bg-amber-50 text-amber-600 border-amber-200",
      registered: false,
    },
    {
      company: "TCS (Digital & Prime)",
      role: "Systems Engineer",
      package: "₹7.0 - ₹9.0 LPA",
      eligibility: "All UG/PG Programs - Batch of 2026",
      status: "Closed",
      deadline: "2026-05-30",
      logoBg: "bg-slate-100 text-slate-600 border-slate-200",
      registered: false,
    },
  ]);

  const handleRegister = (index: number) => {
    setDrives((prev) =>
      prev.map((d, idx) => (idx === index ? { ...d, registered: true } : d))
    );
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Upcoming Placement Drives
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Monitor active hiring schedules, check branch eligibility, package ranges, and submit registrations.
        </p>
      </div>

      {/* Drives List */}
      <div className="space-y-4 max-w-4xl">
        {drives.map((drive, idx) => (
          <div
            key={idx}
            className={`border rounded-3xl p-6 transition-all duration-200 flex flex-col md:flex-row md:items-center justify-between gap-4 ${
              drive.status === "Closed"
                ? "bg-slate-50 border-slate-200/60 opacity-70"
                : "bg-white border-border-dau hover:shadow-lg"
            }`}
          >
            {/* Left side details */}
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2.5">
                <span className={`px-2 py-0.5 text-[8px] font-black uppercase tracking-wider rounded ${drive.logoBg} border`}>
                  {drive.company}
                </span>
                <span className="text-[10px] text-slate-400 font-mono font-bold">
                  Deadline: {drive.deadline}
                </span>
              </div>
              <h3 className="text-xs sm:text-sm font-black text-slate-900 leading-tight">
                {drive.role}
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-1 mt-2 text-[10px] font-bold text-slate-600">
                <p>
                  <strong className="text-slate-400 font-medium">Salary Package:</strong> {drive.package}
                </p>
                <p>
                  <strong className="text-slate-400 font-medium">Eligible Batches:</strong> {drive.eligibility}
                </p>
              </div>
            </div>

            {/* Right side actions */}
            <div className="shrink-0 flex items-center gap-2">
              {drive.status === "Closed" ? (
                <span className="bg-slate-200 text-slate-500 text-[10px] font-black uppercase py-2.5 px-6 rounded-xl select-none">
                  Closed
                </span>
              ) : drive.registered ? (
                <span className="bg-emerald-50 text-emerald-600 border border-emerald-200 text-[10px] font-black uppercase py-2.5 px-6 rounded-xl flex items-center gap-1.5 select-none">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  Registered
                </span>
              ) : (
                <button
                  onClick={() => handleRegister(idx)}
                  className="bg-[#E8400C] text-white hover:bg-[#D7380A] text-[10px] font-black uppercase py-2.5 px-6 rounded-xl shadow-md shadow-[#E8400C]/20 transition-all duration-150"
                >
                  Register Now
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
