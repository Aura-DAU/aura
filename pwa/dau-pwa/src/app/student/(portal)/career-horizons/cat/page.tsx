"use client";

import React from "react";

export default function CatResourcesPage() {
  const sections = [
    {
      name: "Quantitative Aptitude (QA)",
      topics: "Number Systems, Arithmetic (Percentage, Profit & Loss, SI/CI, Ratio, Time & Work), Algebra, Geometry, Mensuration, and Modern Mathematics (Probability, Permutations).",
      books: "Quantitative Aptitude for CAT by Arun Sharma",
    },
    {
      name: "Data Interpretation & Logical Reasoning (DILR)",
      topics: "Caselets, Tables, Graphs (Line, Bar, Pie), Venn Diagrams, Syllogisms, Blood Relations, Seating Arrangements, Coding-Decoding, and Logical Puzzles.",
      books: "How to Prepare for DILR for CAT by Arun Sharma",
    },
    {
      name: "Verbal Ability & Reading Comprehension (VARC)",
      topics: "Reading Comprehension passages, Para-jumbles, Sentence Correction, Summary-based questions, Odd-one-out, and Vocabulary usage.",
      books: "How to Prepare for VARC for CAT by Meenakshi Upadhyay",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          CAT Preparation Resources
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Access syllabus details, preparation roadmaps, and reference materials for the Common Admission Test.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: CAT Sections */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              CAT Exam Syllabus & Structure
            </h2>
            <div className="space-y-4">
              {sections.map((sec, idx) => (
                <div key={idx} className="bg-slate-50 border border-border-dau/50 rounded-2xl p-5 hover:shadow transition-all duration-200">
                  <h3 className="text-xs font-black text-slate-900 mb-1.5 leading-tight">
                    {sec.name}
                  </h3>
                  <p className="text-[10px] text-slate-600 font-medium leading-relaxed mb-3">
                    <strong className="text-slate-800 font-bold block mb-0.5">Syllabus Topics:</strong>
                    {sec.topics}
                  </p>
                  <p className="text-[10px] text-slate-500 font-medium font-mono leading-none">
                    Reference Book: {sec.books}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Timelines & Mock portal */}
        <div className="space-y-6">
          <div className="bg-slate-50 border border-border-dau rounded-3xl p-6 space-y-4">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider">
              Preparation Roadmap
            </h2>
            <div className="space-y-3 text-[10px] font-bold text-slate-700 leading-relaxed">
              <div className="flex gap-2">
                <span className="w-5 h-5 bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] rounded-full flex items-center justify-center shrink-0">1</span>
                <div>
                  <strong className="text-slate-900">Concept Building:</strong> Focus on understanding formulas, arithmetic models, and grammars (Months 1-4).
                </div>
              </div>
              <div className="flex gap-2">
                <span className="w-5 h-5 bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] rounded-full flex items-center justify-center shrink-0">2</span>
                <div>
                  <strong className="text-slate-900">Sectional Mocking:</strong> Solve sectional timers for DILR cased sets and VARC comprehensions (Months 5-7).
                </div>
              </div>
              <div className="flex gap-2">
                <span className="w-5 h-5 bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] rounded-full flex items-center justify-center shrink-0">3</span>
                <div>
                  <strong className="text-slate-900">Full Mocks & Analysis:</strong> Write complete mock tests weekly, analyze errors, and adjust strategies (Months 8-10).
                </div>
              </div>
            </div>
          </div>

          <div className="bg-orange-50 border border-orange-200/50 rounded-3xl p-6 text-xs text-slate-700">
            <h2 className="text-sm font-black text-[#E8400C] uppercase tracking-wider mb-2">
              CAT Mock Portal
            </h2>
            <p className="leading-relaxed mb-4">
              Practice CAT-style timed tests to build speed and accuracy. Click below to begin sectional tests.
            </p>
            <a
              href="#"
              className="bg-[#E8400C] text-white text-[10px] font-black uppercase py-2.5 px-6 rounded-xl shadow-md shadow-[#E8400C]/20 transition-all duration-150 inline-block text-center"
            >
              Start Free DILR Test
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
