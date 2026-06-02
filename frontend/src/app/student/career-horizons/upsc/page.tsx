"use client";

import React from "react";

export default function UpscMaterialPage() {
  const prelimsSyllabus = [
    { paper: "General Studies I (GS-I)", desc: "Current affairs, History of India & Indian National Movement, Indian & World Geography, Indian Polity & Governance, Economic & Social Development, General Science, and Environmental Ecology." },
    { paper: "Civil Services Aptitude Test (CSAT)", desc: "Comprehension, interpersonal skills, logical reasoning, analytical ability, decision-making, general mental ability, and basic numeracy (class 10 level)." },
  ];

  const ncertBooks = [
    { subject: "History", books: "Class 11 & 12 (Ancient, Medieval, Modern India by Bipin Chandra)." },
    { subject: "Geography", books: "Class 11 & 12 (Fundamentals of Physical Geography, India: Physical Environment)." },
    { subject: "Polity", books: "Class 11 & 12 (Indian Constitution at Work) + Laxmikanth's Indian Polity." },
    { subject: "Economy", books: "Class 11 (Indian Economic Development) & Class 12 (Macroeconomics)." },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          UPSC Preparation Materials
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Access syllabus maps, basic NCERT reference guides, and general studies resources for Civil Services Examinations.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Prelims GS/CSAT */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              UPSC Prelims Syllabus Mapping
            </h2>
            <div className="space-y-4">
              {prelimsSyllabus.map((p, idx) => (
                <div key={idx} className="bg-slate-50 border border-border-dau/50 rounded-2xl p-5">
                  <h3 className="text-xs font-black text-slate-900 mb-1.5 leading-tight">
                    {p.paper}
                  </h3>
                  <p className="text-[10px] text-slate-600 font-medium leading-relaxed">
                    {p.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              Essential NCERT Reference Books
            </h2>
            <div className="border border-border-dau rounded-2xl overflow-hidden text-xs sm:text-sm">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 border-b border-border-dau font-bold text-slate-800">
                    <th className="px-4 py-3 w-1/3">Subject</th>
                    <th className="px-4 py-3">Recommended NCERT Reading</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {ncertBooks.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-4 py-3 font-bold text-slate-800 bg-slate-50/20">{item.subject}</td>
                      <td className="px-4 py-3 text-slate-600 font-medium leading-relaxed">{item.books}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: General Studies resources */}
        <div className="space-y-6">
          <div className="bg-slate-50 border border-border-dau rounded-3xl p-6 space-y-4">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider">
              UPSC preparation tips
            </h2>
            <div className="space-y-3 text-[10px] font-bold text-slate-700 leading-relaxed">
              <div className="flex gap-2">
                <span className="w-5 h-5 bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] rounded-full flex items-center justify-center shrink-0">1</span>
                <div>
                  <strong className="text-slate-900">Newspaper Reading:</strong> Read the Hindu or Indian Express daily, focusing on national news and editorials.
                </div>
              </div>
              <div className="flex gap-2">
                <span className="w-5 h-5 bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] rounded-full flex items-center justify-center shrink-0">2</span>
                <div>
                  <strong className="text-slate-900">Answer Writing:</strong> Start daily mains answer writing practice for GS paper topics (6 months prior to prelims).
                </div>
              </div>
              <div className="flex gap-2">
                <span className="w-5 h-5 bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] rounded-full flex items-center justify-center shrink-0">3</span>
                <div>
                  <strong className="text-slate-900">Option Selection:</strong> Choose optional subjects based on graduation backgrounds or personal reading interests.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
