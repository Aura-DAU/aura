import React from "react";
import Link from "next/link";

export default function AlumniPage() {
  const sections = [
    {
      title: "Alumni Directory",
      desc: "Connect with graduates across domains, view their company profiles, work sectors, and contact info.",
      href: "/student/alumni",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      )
    },
    {
      title: "Regional Chapters",
      desc: "Information about regional chapters (Ahmedabad, Gandhinagar, Mumbai, Bangalore) and local networking meets.",
      href: "/student/alumni/chapters",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      )
    },
    {
      title: "Mentorship & Events",
      desc: "Engage with standard alumni-student mentoring circles, campus talks, reconnect meetings, and webinar schedules.",
      href: "/student/alumni/connect",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Alumni Network
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Stay connected with the Dhirubhai Ambani University alumni network, regional chapters, and mentorship projects.
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
