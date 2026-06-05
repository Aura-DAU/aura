"use client";

import React from "react";

export default function MsPhdAbroadPage() {
  const steps = [
    { title: "Standardized Tests", desc: "Write GRE (for US universities) and English proficiency tests like TOEFL or IELTS. Target scores: GRE > 320, TOEFL > 100." },
    { title: "SOP & Resume Preparation", desc: "Draft a 1-page Statement of Purpose detailing research experience, interests, and why you choose that specific university." },
    { title: "Letters of Recommendation", desc: "Secure 3 letters of recommendation from faculty mentors or project advisors who have closely observed your academic/research skills." },
    { title: "University Shortlisting", desc: "Divide target universities into Ambitious, Moderate, and Safe categories based on your CGPA and test profiles." },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          MS & PhD Abroad Guidelines
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Detailed roadmaps for higher study applications, standardized test guidance, Statement of Purpose (SOP) drafting, and LOR tips.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Guidelines */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              Application Process Checklist
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {steps.map((step, idx) => (
                <div key={idx} className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 hover:shadow transition-all duration-200">
                  <span className="w-6 h-6 rounded-full bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] text-[10px] font-black flex items-center justify-center mb-3">
                    {idx + 1}
                  </span>
                  <h3 className="text-xs font-black text-slate-900 mb-1 leading-tight">
                    {step.title}
                  </h3>
                  <p className="text-[10px] text-slate-500 font-medium leading-relaxed mt-1">
                    {step.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Key Timelines */}
        <div className="space-y-6">
          <div className="bg-slate-50 border border-border-dau rounded-3xl p-6 space-y-4">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider">
              Application Timeline (Fall Intake)
            </h2>
            <div className="space-y-3 text-[10px] font-bold text-slate-700 leading-relaxed">
              <div className="bg-white p-3.5 rounded-xl border border-border-dau/50">
                <strong className="text-slate-900 block mb-0.5">May - July:</strong> Prepare for GRE/TOEFL. Gather initial university lists.
              </div>
              <div className="bg-white p-3.5 rounded-xl border border-border-dau/50">
                <strong className="text-slate-900 block mb-0.5">August - September:</strong> Write tests. Draft Statement of Purpose (SOP) and request LORs.
              </div>
              <div className="bg-white p-3.5 rounded-xl border border-border-dau/50">
                <strong className="text-slate-900 block mb-0.5">October - December:</strong> Submit online applications (deadlines range from Dec 1 to Jan 15).
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
