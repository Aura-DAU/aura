import React from "react";
import Link from "next/link";

export default function CareerHorizonsPage() {
  const sections = [
    {
      title: "GATE Resources",
      desc: "Mock tests, solved previous papers, recommended reference books, and strategy guidelines for GATE.",
      href: "/student/career-horizons/gate",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
        </svg>
      )
    },
    {
      title: "CAT Resources",
      desc: "Quantitative aptitude syllabus, verbal ability worksheets, and competitive mock paper sets for CAT aspirants.",
      href: "/student/career-horizons/cat",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 002 2h2a2 2 0 002-2z" />
        </svg>
      )
    },
    {
      title: "UPSC Material",
      desc: "Prelims and mains strategy recommendations, current affairs analysis, and reference directories.",
      href: "/student/career-horizons/upsc",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      )
    },
    {
      title: "MS / PhD Abroad",
      desc: "Guidance on application processes, standard recommendation letters, GRE/TOEFL advice, and universities mapping.",
      href: "/student/career-horizons/ms-phd",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 002 2h1.5A2.5 2.5 0 0019 9.5V8a2 2 0 00-2-2h-1a2 2 0 01-2-2V3.055M11 20.055V18a2 2 0 00-2-2h-1a2 2 0 01-2-2v-1" />
        </svg>
      )
    },
    {
      title: "Other Specialized Exams",
      desc: "Materials and preparation guidelines for specialized defense, state banking, and engineering competitive services.",
      href: "/student/career-horizons/others",
      icon: (
        <svg className="w-6 h-6 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Other Career Horizons
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Explore comprehensive prep guides and reference links for competitive exams, civil services, and higher research studies.
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
