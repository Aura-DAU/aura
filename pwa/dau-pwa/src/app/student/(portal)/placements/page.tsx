import React from "react";
import Link from "next/link";

export default function PlacementsPage() {
  const sections = [
    {
      title: "Placement Stats & Info",
      desc: "Overview of previous years' placement highlights, package trends, average CTC, and recruiting sectors.",
      href: "/student/placements",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
        </svg>
      )
    },
    {
      title: "Upcoming Drives",
      desc: "Calendar details of companies visiting campus, registration requirements, eligible batches, and timelines.",
      href: "/student/placements/drives",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      title: "Company Profiles",
      desc: "Comprehensive database of visiting recruiters, their package details, job profiles, and select standard criteria.",
      href: "/student/placements/companies",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      )
    },
    {
      title: "Preparation Material",
      desc: "Access mock tests, standard interview questions, coding preparation guides, and preparation insights.",
      href: "/student/placements/preparation",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Placements
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Support your entire placement journey from preparation materials to live campus drives.
        </p>
      </div>

      {/* Grid of options */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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
