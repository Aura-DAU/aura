"use client";

import React, { useState, useEffect } from "react";
import { fetchStudentServiceDocument } from "@/services/studentServices";
import MarkdownRenderer from "@/components/ui/MarkdownRenderer";

const COMMITTEES_FALLBACK = `### student committees
- **Academic Committee:** Works on academic matters, grading policies, and registry interface.
- **Cultural Committee:** Organizes festivals (Tarang, Synapse, Independence Day).
- **Sports Committee:** Drives sports meets (Concours, DCL cricket league).
- **Cafeteria Committee:** Monitors hygiene and food prices.`;

export default function CommitteesPage() {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadContent() {
      try {
        const res = await fetchStudentServiceDocument({ fileName: "dean_students_tab.md" });
        if (res.success && res.content) {
          setContent(res.content);
        } else {
          setContent(COMMITTEES_FALLBACK);
        }
      } catch {
        setContent(COMMITTEES_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadContent();
  }, []);

  const sbgCore = [
    { name: "Yash Judal", role: "Convenor", email: "convener_student_government@dau.ac.in" },
    { name: "Dev Sanghani", role: "Deputy Convenor", email: "dy_convener_student_government@dau.ac.in" },
    { name: "Madhav Bhatt", role: "Treasurer", email: "treasurer_student_government@dau.ac.in" },
    { name: "Siddh Shah", role: "Secretary", email: "secretary_student_government@dau.ac.in" },
  ];

  const rbgCore = [
    { name: "Bhavin Makwana", role: "Convenor" },
    { name: "Dhiraj Golhar", role: "Deputy Convener" },
    { name: "Adiba Khan", role: "Secretary" },
    { name: "Pronay Dey", role: "Treasurer" },
    { name: "Himani", role: "Diversity & Well-Being Officer" },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Student Committees & Government
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Meet the Student Body Government (SBG), Research Body Government (RBG), and the 8 official student committees.
        </p>
      </div>

      {/* Grid: Left - Core Student Gov Cards, Right - Full Committee Descriptions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left column: Student Gov & Research Gov */}
        <div className="space-y-6">
          {/* SBG Card */}
          <div className="bg-white border border-border-dau rounded-3xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
              <span className="p-2 bg-[#E8400C]/10 rounded-xl text-[#E8400C]">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </span>
              <div>
                <h2 className="text-sm font-black text-slate-900 leading-tight">Student Body Government</h2>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">SBG Core Team</p>
              </div>
            </div>

            <div className="space-y-3">
              {sbgCore.map((member, idx) => (
                <div key={idx} className="bg-slate-50 rounded-xl p-3 border border-border-dau/40">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-black text-slate-800">{member.name}</span>
                    <span className="text-[9px] font-black uppercase text-[#E8400C] bg-orange-50 border border-orange-200/50 px-1.5 py-0.5 rounded">
                      {member.role}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-400 font-mono mt-1 select-text">{member.email}</p>
                </div>
              ))}
            </div>
          </div>

          {/* RBG Card */}
          <div className="bg-white border border-border-dau rounded-3xl p-6 shadow-sm">
            <div className="flex items-center gap-2 mb-4 border-b border-slate-100 pb-3">
              <span className="p-2 bg-blue-500/10 rounded-xl text-blue-600">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </span>
              <div>
                <h2 className="text-sm font-black text-slate-900 leading-tight">Research Body Government</h2>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">RBG PhD Core</p>
              </div>
            </div>

            <div className="space-y-3">
              {rbgCore.map((member, idx) => (
                <div key={idx} className="bg-slate-50 rounded-xl p-3 border border-border-dau/40">
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-black text-slate-800">{member.name}</span>
                    <span className="text-[9px] font-black uppercase text-blue-500 bg-blue-50 border border-blue-200/50 px-1.5 py-0.5 rounded">
                      {member.role}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right column: Aggregated markdown descriptions of the 8 committees */}
        <div className="lg:col-span-2">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              Official Student Committees Guidelines
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-xs sm:text-sm text-slate-700">
                <MarkdownRenderer content={content} />
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
