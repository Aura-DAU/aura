"use client";

import React from "react";

export default function PreparationMaterialPage() {
  const prepSheets = [
    {
      title: "Data Structures & Algorithms Sheet",
      desc: "Top 150 curated coding problems covering arrays, trees, heaps, dynamic programming, and system designs.",
      topics: ["Arrays", "Linked Lists", "Trees", "DP", "Graphs"],
      links: "https://github.com",
    },
    {
      title: "Quantitative Aptitude & Logic Guides",
      desc: "Practice worksheets for probability, combinations, quantitative reasoning, and puzzles frequently asked in initial rounds.",
      topics: ["Puzzles", "Probability", "Permutations", "Speed Math"],
      links: "#",
    },
    {
      title: "Resume & Portfolio Guidelines",
      desc: "Standard guidelines for framing descriptions, project listings, and university-approved resume formatting styles.",
      topics: ["Formatting", "Action Verbs", "Project Framing"],
      links: "#",
    },
  ];

  const spcContacts = [
    { name: "Jevik Rakholiya", role: "Convener", branch: "B.Tech (ICT) 2023", email: "spc@dau.ac.in" },
    { name: "Chaitanya Vats", role: "Deputy Convener", branch: "B.Tech (ICT) 2023" },
    { name: "Mr. Souvik Sarkar", role: "Head - Career Planning & Placement", branch: "Administration", email: "head_cpm@dau.ac.in", phone: "+91 9320301228" },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Placement Preparation Materials
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Access coding worksheets, quantitative logic sheets, resume guidelines, and contact the Student Placement Cell.
        </p>
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Prep Sheets */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              Curated Preparation Sheets
            </h2>

            <div className="space-y-4">
              {prepSheets.map((sheet, idx) => (
                <div
                  key={idx}
                  className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 hover:shadow transition-all duration-200"
                >
                  <h3 className="text-xs font-black text-slate-900 mb-1.5 leading-tight">
                    {sheet.title}
                  </h3>
                  <p className="text-[10px] text-slate-500 font-medium leading-relaxed mb-4">
                    {sheet.desc}
                  </p>

                  <div className="flex flex-wrap gap-1.5 mb-4">
                    {sheet.topics.map((t, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-[8px] font-black uppercase tracking-wider rounded bg-white border border-border-dau text-slate-500"
                      >
                        {t}
                      </span>
                    ))}
                  </div>

                  <a
                    href={sheet.links}
                    className="inline-flex items-center gap-1.5 text-[10px] font-black text-[#E8400C] hover:underline"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                    Access Reference Material
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: SPC Representatives */}
        <div className="space-y-4">
          <div className="bg-slate-50 border border-border-dau rounded-3xl p-6">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider mb-4">
              Placement Cell Contacts
            </h2>

            <div className="space-y-4">
              {spcContacts.map((contact, idx) => (
                <div
                  key={idx}
                  className="bg-white border border-border-dau rounded-2xl p-4 hover:shadow-md transition-all duration-200"
                >
                  <div className="flex justify-between items-start">
                    <h3 className="text-xs font-black text-slate-900 leading-tight">
                      {contact.name}
                    </h3>
                    <span className="text-[8px] font-black uppercase text-[#E8400C] bg-orange-50 border border-orange-200/50 px-1.5 py-0.5 rounded">
                      {contact.role}
                    </span>
                  </div>
                  <p className="text-[9px] text-slate-400 font-bold mt-1 uppercase tracking-wider">
                    {contact.branch}
                  </p>
                  <div className="space-y-1 mt-3 pt-3 border-t border-slate-50 text-[9px] font-medium text-slate-500 font-mono select-text">
                    {contact.email && <p>Email: {contact.email}</p>}
                    {contact.phone && <p>Phone: {contact.phone}</p>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
