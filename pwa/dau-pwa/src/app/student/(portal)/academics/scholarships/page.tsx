"use client";

import React, { useState } from "react";

export default function ScholarshipsPage() {
  const [selectedScheme, setSelectedScheme] = useState<"merit" | "mcm" | "external">("merit");

  const schemes = {
    merit: {
      title: "University Merit Scholarships",
      desc: "Awarded automatically to the top rankers of each branch based on academic performance in the preceding year.",
      details: [
        { key: "Eligibility", val: "Top 5% students in each branch based on SGPI/CGPI (minimum 9.0 CGPI)." },
        { key: "Award Amount", val: "Full (100%) tuition fee waiver for the respective academic year." },
        { key: "Renewal Criteria", val: "Must maintain a minimum of 9.0 CGPI in subsequent semesters without any backlogs." },
      ],
      steps: "No application required. The scholarship registry publishes the merit list at the start of the autumn semester.",
    },
    mcm: {
      title: "Merit-cum-Means (MCM) Scholarships",
      desc: "Supports academically bright students from financially constrained backgrounds with partial or full tuition concessions.",
      details: [
        { key: "Eligibility", val: "CGPI of 7.0 or above, and family annual income below ₹6,00,000/-." },
        { key: "Award Amount", val: "50% or 100% tuition fee concession based on financial need assessment." },
        { key: "Required Docs", val: "IT Return filings of parents, income certificate, and academic transcripts." },
      ],
      steps: "Submit the MCM Scholarship Application Form (available at the student counter) along with income proof by August 31st.",
    },
    external: {
      title: "Government & Corporate Schemes",
      desc: "Assists students in applying for state/central government fellowships and corporate sponsorships.",
      details: [
        { key: "MYSY Scheme", val: "Gujarat State Mukhyamantri Yuva Swavalamban Yojana providing up to ₹50,000/- or 50% fee concession." },
        { key: "National Scholarship Portal", val: "Post-matric scholarships for SC/ST/OBC and minority candidates from various central ministries." },
        { key: "Corporate Grants", val: "Sponsorships from foundations like Reliance Foundation (undergraduate & postgraduate programs)." },
      ],
      steps: "Apply directly on the respective government (MYSY/NSP) or corporate portals. Submit verified forms to the DAU Registry for university endorsement.",
    },
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Scholarships and Student Support
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Explore financial aid opportunities, merit-based tuition waivers, and external government scholarships.
        </p>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Scheme Pills Navigation */}
        <div className="space-y-3">
          <div className="bg-slate-50 border border-border-dau/60 rounded-3xl p-5 space-y-2">
            <h2 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3 px-2">
              Select Scholarship Category
            </h2>
            <button
              onClick={() => setSelectedScheme("merit")}
              className={`w-full text-left px-4 py-3 rounded-2xl text-xs font-black uppercase transition-all duration-150 ${
                selectedScheme === "merit"
                  ? "bg-[#E8400C] text-white shadow-md shadow-[#E8400C]/20"
                  : "bg-white text-slate-700 hover:bg-slate-200 border border-border-dau/40"
              }`}
            >
              Merit Scholarships
            </button>
            <button
              onClick={() => setSelectedScheme("mcm")}
              className={`w-full text-left px-4 py-3 rounded-2xl text-xs font-black uppercase transition-all duration-150 ${
                selectedScheme === "mcm"
                  ? "bg-[#E8400C] text-white shadow-md shadow-[#E8400C]/20"
                  : "bg-white text-slate-700 hover:bg-slate-200 border border-border-dau/40"
              }`}
            >
              Merit-cum-Means
            </button>
            <button
              onClick={() => setSelectedScheme("external")}
              className={`w-full text-left px-4 py-3 rounded-2xl text-xs font-black uppercase transition-all duration-150 ${
                selectedScheme === "external"
                  ? "bg-[#E8400C] text-white shadow-md shadow-[#E8400C]/20"
                  : "bg-white text-slate-700 hover:bg-slate-200 border border-border-dau/40"
              }`}
            >
              Government / Corporate
            </button>
          </div>
        </div>

        {/* Right Scheme Details Panel */}
        <div className="md:col-span-2">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
            <div>
              <h2 className="text-base font-bold text-slate-900 mb-1 border-l-4 border-[#E8400C] pl-3">
                {schemes[selectedScheme].title}
              </h2>
              <p className="text-xs text-text-muted mt-1 leading-relaxed">
                {schemes[selectedScheme].desc}
              </p>
            </div>

            {/* Scheme Metadata Table */}
            <div className="border border-border-dau rounded-2xl overflow-hidden">
              <table className="w-full text-left border-collapse text-xs sm:text-sm">
                <tbody className="divide-y divide-slate-100 bg-white">
                  {schemes[selectedScheme].details.map((detail, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 transition-colors">
                      <td className="px-4 py-3 font-bold text-slate-900 w-1/3 bg-slate-50/50">{detail.key}</td>
                      <td className="px-4 py-3 text-slate-600 font-medium">{detail.val}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* How to Apply Section */}
            <div className="bg-orange-50/50 border border-orange-200/50 rounded-2xl p-4 sm:p-5">
              <h3 className="text-xs font-black text-[#E8400C] uppercase tracking-wider mb-1.5">
                How to Apply
              </h3>
              <p className="text-xs text-slate-700 font-medium leading-relaxed">
                {schemes[selectedScheme].steps}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
