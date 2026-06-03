import React from "react";
import Link from "next/link";

export default function CocurricularPage() {
  const sections = [
    {
      title: "Student Clubs",
      desc: "Explore cultural, technical, and sports clubs, their objectives, convenors, and how to register.",
      href: "/student/cocurricular/clubs",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    },
    {
      title: "Daily Campus Events",
      desc: "Stay updated with daily seminars, workshops, sports gatherings, and technical bootcamps.",
      href: "/student/cocurricular/events",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      title: "Student Committees & Gov",
      desc: "Details about Student Body Government, active student committees, and their respective delegates.",
      href: "/student/cocurricular/committees",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Co-curricular Activities
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Engage with student clubs, committees, daily activities, workshops, and sports gathers.
        </p>
      </div>

      {/* Grid of options */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sections.map((sec, idx) => (
          <Link
            key={idx}
            href={sec.href}
            className="group block bg-white border border-border-dau rounded-xl p-5 hover:border-primary-dau/40 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 shadow-sm"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2.5 bg-background rounded-lg group-hover:scale-105 transition-transform duration-200">
                {sec.icon}
              </div>
              <svg className="w-4 h-4 text-text-muted group-hover:text-primary-dau group-hover:translate-x-0.5 transition-all duration-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </div>
            <h3 className="text-sm font-bold text-foreground mb-1.5 group-hover:text-primary-dau transition-colors duration-150">
              {sec.title}
            </h3>
            <p className="text-xs text-text-muted leading-relaxed">
              {sec.desc}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
