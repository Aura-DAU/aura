"use client";

import React from "react";

export default function OtherExamsPage() {
  const exams = [
    {
      name: "Defense Services (CDS / AFCAT)",
      desc: "Careers in Indian Air Force (Technical branch), Army, and Navy. Focus on general knowledge, elementary mathematics, and english grammar.",
      eligibility: "B.Tech students of any branch. Final year students can apply.",
    },
    {
      name: "Banking Services (SBI PO / IBPS)",
      desc: "Probationary Officer posts. Focus on fast quantitative aptitude calculations, logical puzzles, and English vocabulary usage.",
      eligibility: "Any graduate degree. Age limit: 21 - 30 years.",
    },
    {
      name: "Engineering Services (IES / ESE)",
      desc: "Union Public Service Commission engineering positions. Detailed technical subjective and objective papers in Electronics & Telecom, Electrical, Civil, or Mechanical.",
      eligibility: "B.Tech in Electronics & VLSI, ECE, or allied disciplines.",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Other Competitive Examinations
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Explore reference guides and syllabus maps for banking, defense, and public sector engineering services.
        </p>
      </div>

      {/* Grid of Exams */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl">
        {exams.map((exam, idx) => (
          <div
            key={idx}
            className="bg-white border border-border-dau rounded-3xl p-6 hover:shadow-lg transition-all duration-200 flex flex-col justify-between"
          >
            <div>
              <h3 className="text-xs font-black text-slate-900 mb-2 leading-tight">
                {exam.name}
              </h3>
              <p className="text-[10px] text-slate-500 font-medium leading-relaxed mb-4">
                {exam.desc}
              </p>
            </div>
            <div className="text-[9px] font-bold text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-100">
              <strong className="text-slate-700 block mb-0.5">Eligibility:</strong>
              {exam.eligibility}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
