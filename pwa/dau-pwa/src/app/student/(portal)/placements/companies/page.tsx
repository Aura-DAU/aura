"use client";

import React, { useState } from "react";

export default function CompanyProfilesPage() {
  const [searchQuery, setSearchQuery] = useState("");

  const companies = [
    {
      name: "Google India",
      package: "₹38.5 - ₹48.0 LPA",
      avgHires: "10 - 15 students",
      criteria: "Minimum 8.0 CPI. No active backlogs. Focus on strong DSA, System Design, and OS.",
      logoBg: "bg-red-50 text-red-600 border-red-200",
    },
    {
      name: "Microsoft",
      package: "₹30.0 - ₹44.0 LPA",
      avgHires: "15 - 25 students",
      criteria: "Minimum 7.5 CPI. Open to all B.Tech and M.Tech streams. Focus on problem solving.",
      logoBg: "bg-blue-50 text-blue-600 border-blue-200",
    },
    {
      name: "Morgan Stanley",
      package: "₹25.0 - ₹29.5 LPA",
      avgHires: "8 - 12 students",
      criteria: "Minimum 7.0 CPI. Focus on Java OOPs, DBMS/SQL, and competitive coding speed.",
      logoBg: "bg-purple-50 text-purple-600 border-purple-200",
    },
    {
      name: "Oracle (OFSS)",
      package: "₹18.0 - ₹22.0 LPA",
      avgHires: "20 - 30 students",
      criteria: "Minimum 6.5 CPI. Strong database knowledge, computer networks, and scripting.",
      logoBg: "bg-red-100 text-red-700 border-red-200",
    },
    {
      name: "Atlassian",
      package: "₹52.0 - ₹57.5 LPA",
      avgHires: "3 - 5 students",
      criteria: "Minimum 8.5 CPI. Exceptional algorithmic foundations, web protocols, and networks.",
      logoBg: "bg-blue-100 text-blue-700 border-blue-200",
    },
    {
      name: "Sprinklr",
      package: "₹30.0 LPA",
      avgHires: "5 - 8 students",
      criteria: "Minimum 7.5 CPI. Excellent knowledge of web applications, cloud hosting, and scalability.",
      logoBg: "bg-amber-50 text-amber-700 border-amber-200",
    },
  ];

  const filteredCompanies = companies.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Recruiting Company Profiles
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Search historically visiting company requirements, package slabs, and core criteria details.
          </p>
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-72">
          <svg className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search company profiles..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-border-dau/80 rounded-2xl pl-10 pr-4 py-2.5 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#E8400C] focus:ring-1 focus:ring-[#E8400C]/20 transition-all duration-200"
          />
        </div>
      </div>

      {/* Companies Grid */}
      {filteredCompanies.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCompanies.map((c, idx) => (
            <div
              key={idx}
              className="bg-white border border-border-dau rounded-3xl p-6 hover:shadow-xl hover:shadow-slate-100 hover:-translate-y-0.5 transition-all duration-200 flex flex-col justify-between"
            >
              <div>
                <span className={`w-10 h-10 rounded-2xl flex items-center justify-center font-black text-xs border ${c.logoBg} mb-4`}>
                  {c.name[0]}
                </span>
                <h3 className="text-sm font-black text-slate-900 mb-1.5 leading-tight">
                  {c.name}
                </h3>
                <div className="space-y-1 mt-3 text-[10px] font-bold text-slate-600">
                  <p>
                    <strong className="text-slate-400 font-medium">Standard Package:</strong> {c.package}
                  </p>
                  <p>
                    <strong className="text-slate-400 font-medium">Avg Intake:</strong> {c.avgHires}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-slate-50 text-[10px] text-slate-500 font-medium leading-relaxed">
                <strong className="text-slate-800 font-bold block mb-0.5">Evaluation Focus:</strong>
                {c.criteria}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <svg className="w-8 h-8 text-slate-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs text-slate-500 font-bold">No companies found matching your search query.</p>
        </div>
      )}
    </div>
  );
}
