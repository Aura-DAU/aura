import React from "react";
import Link from "next/link";

export default function AcademicsPage() {
  const academicServices = [
    {
      title: "Course Info",
      desc: "Access syllabus, faculty details, resources.",
      href: "/student/academics/courses",
      iconBg: "bg-orange-100 border border-orange-200 text-[#E8400C]",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      )
    },
    {
      title: "Timetable",
      desc: "Check your class schedule for the current semester.",
      href: "/student/academics/timetable",
      iconBg: "bg-blue-100 border border-blue-200 text-blue-600",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      )
    },
    {
      title: "Academic Calendar",
      desc: "View key dates, holidays, exams, deadlines.",
      href: "/student/academics/calendar",
      iconBg: "bg-teal-100 border border-teal-200 text-teal-600",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      )
    },
    {
      title: "Policies & Guidelines",
      desc: "Important BMP, BTP, Leave and disciplinary guidelines.",
      href: "/student/academics/policies",
      iconBg: "bg-purple-100 border border-purple-200 text-purple-600",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      )
    },
    {
      title: "Examinations",
      desc: "Rules for evaluation, grade scales, and passing standards.",
      href: "/student/academics/examinations",
      iconBg: "bg-emerald-100 border border-emerald-200 text-emerald-600",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 00-2 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      )
    },
    {
      title: "Hostel Rules",
      desc: "Hostel residency rules, procedures, and contacts.",
      href: "/student/academics/hostel",
      iconBg: "bg-rose-100 border border-rose-200 text-rose-600",
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="border-b border-[#E2E8F0] pb-4">
        <h1 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900">
          Academics
        </h1>
        <p className="text-xs sm:text-sm text-slate-500 font-medium mt-1">
          Explore course specifications, timetables, calendar events, and hostel guidelines.
        </p>
      </div>

      {/* Grid Layout of Services */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {academicServices.map((service, idx) => (
          <div
            key={idx}
            className="flex flex-col bg-white border border-[#E2E8F0] rounded-[24px] p-6 hover:shadow-xl hover:shadow-slate-200/50 hover:-translate-y-0.5 transition-all duration-200"
          >
            {/* Colored Icon container */}
            <div className={`w-12 h-12 rounded-[16px] flex items-center justify-center mb-4 ${service.iconBg}`}>
              {service.icon}
            </div>

            {/* Content info */}
            <h3 className="text-base font-black text-slate-900 mb-1">
              {service.title}
            </h3>
            <p className="text-xs text-slate-500 font-medium leading-relaxed flex-1">
              {service.desc}
            </p>

            {/* View Details solid orange button */}
            <Link
              href={service.href}
              className="bg-[#E8400C] text-white text-xs font-black py-3 px-4 rounded-[16px] hover:bg-[#D7380A] shadow-md shadow-[#E8400C]/15 transition-all duration-150 text-center w-full block mt-5"
            >
              View Details
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
