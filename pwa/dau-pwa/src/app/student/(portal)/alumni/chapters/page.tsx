"use client";

import React, { useState, useEffect } from "react";
import { fetchStudentServiceDocument } from "@/lib/api/studentServices.action";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";

const CHAPTERS_FALLBACK = `### alumni chapters
- **Gandhinagar-Ahmedabad Chapter:** Convenor: Yash Shah. Annual meets in December.
- **Bangalore Chapter:** Convenor: Rahul Patel. Networking mixers in July.
- **Mumbai Chapter:** Convenor: Priya Sharma. Focus on fintech and consulting networking.`;

export default function AlumniChaptersPage() {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadContent() {
      try {
        const res = await fetchStudentServiceDocument({ fileName: "alumni_chapter_membership_drive.md" });
        if (res.success && res.content) {
          setContent(res.content);
        } else {
          setContent(CHAPTERS_FALLBACK);
        }
      } catch {
        setContent(CHAPTERS_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadContent();
  }, []);

  const activeChapters = [
    { city: "Gandhinagar - Ahmedabad", activeMeets: "Annual Reunion Meet 2026 (Dec 27)", contact: "ahd-chapter@dau.ac.in" },
    { city: "Bangalore (Silicon Valley)", activeMeets: "Tech Mixer & Networking Dinner (July 12)", contact: "blr-chapter@dau.ac.in" },
    { city: "Mumbai (Fintech Hub)", activeMeets: "Fintech Career Panel Discussion (Sept 05)", contact: "bom-chapter@dau.ac.in" },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Alumni Regional Chapters
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Explore local chapters, membership drives, regional meetups, and local contact details.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Chapters details */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              Alumni Chapter & Membership Initiatives
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={content} />
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Local Meets */}
        <div className="space-y-4">
          <div className="bg-slate-50 border border-border-dau rounded-3xl p-6">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider mb-4">
              Active Regional Chapters
            </h2>
            <div className="space-y-4">
              {activeChapters.map((ch, idx) => (
                <div
                  key={idx}
                  className="bg-white border border-border-dau rounded-2xl p-4 hover:shadow-md transition-all duration-200"
                >
                  <h3 className="text-xs font-black text-slate-900 mb-1 leading-tight">
                    {ch.city}
                  </h3>
                  <p className="text-[9px] text-[#E8400C] font-bold mt-1 uppercase tracking-wider">
                    {ch.activeMeets}
                  </p>
                  <p className="text-[10px] text-slate-500 font-mono mt-2 pt-2 border-t border-slate-50 select-text">
                    Email: {ch.contact}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
