"use client";

import React, { useState, useEffect } from "react";
import { getFacultyList, FacultyMember } from "@/lib/api/studentServices.action";
import { fetchStudentServiceDocument } from "@/lib/api/studentServices.action";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";

export default function FacultyPage() {
  const [faculty, setFaculty] = useState<FacultyMember[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);

  // Detail Modal State
  const [selectedMember, setSelectedMember] = useState<FacultyMember | null>(null);
  const [detailContent, setDetailContent] = useState("");
  const [loadingDetails, setLoadingDetails] = useState(false);

  useEffect(() => {
    async function loadFaculty() {
      try {
        const list = await getFacultyList();
        setFaculty(list);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadFaculty();
  }, []);

  const filteredFaculty = faculty.filter((member) => {
    const query = searchQuery.toLowerCase();
    return (
      member.name.toLowerCase().includes(query) ||
      member.specialization.toLowerCase().includes(query) ||
      member.designation.toLowerCase().includes(query)
    );
  });

  const handleOpenDetails = async (member: FacultyMember) => {
    setSelectedMember(member);
    setLoadingDetails(true);
    setDetailContent("");
    try {
      const res = await fetchStudentServiceDocument({ fileName: member.fileName });
      if (res.success && res.content) {
        setDetailContent(res.content);
      } else {
        setDetailContent("Could not load biography details.");
      }
    } catch {
      setDetailContent("Error loading biography details.");
    } finally {
      setLoadingDetails(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
            Faculty & Department Discovery
          </h1>
          <p className="text-sm text-text-muted mt-1">
            Search the directory to locate faculty blocks, specializations, office hours, and research topics.
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative w-full sm:w-72">
          <svg className="absolute left-3.5 top-3 w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            placeholder="Search name, topic, office..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white border border-border-dau/80 rounded-2xl pl-10 pr-4 py-2.5 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#E8400C] focus:ring-1 focus:ring-[#E8400C]/20 transition-all duration-200"
          />
        </div>
      </div>

      {/* Grid of Faculty cards */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="animate-pulse bg-slate-50 border border-border-dau rounded-3xl p-6 h-48 space-y-4">
              <div className="h-6 bg-slate-100 rounded w-2/3" />
              <div className="h-4 bg-slate-100 rounded w-1/2" />
              <div className="h-10 bg-slate-100 rounded w-full mt-4" />
            </div>
          ))}
        </div>
      ) : filteredFaculty.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredFaculty.map((member, idx) => (
            <div
              key={idx}
              className="bg-white border border-border-dau rounded-3xl p-6 hover:shadow-xl hover:shadow-slate-100 hover:-translate-y-0.5 transition-all duration-200 flex flex-col justify-between"
            >
              <div>
                <span className="text-[9px] font-black tracking-wide uppercase text-slate-400 block mb-1">
                  {member.designation}
                </span>
                <h3 className="text-sm font-black text-slate-900 mb-2 leading-tight">
                  {member.name}
                </h3>
                <p className="text-[10px] text-slate-500 font-medium line-clamp-2 leading-relaxed mb-4">
                  <strong>Research:</strong> {member.specialization}
                </p>
              </div>

              <div className="space-y-2 mt-4 pt-4 border-t border-slate-50 text-[10px] font-bold text-slate-600">
                <div className="flex items-center gap-2">
                  <svg className="w-3.5 h-3.5 text-[#E8400C] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                  <span>{member.office}</span>
                </div>
                <div className="flex items-center gap-2">
                  <svg className="w-3.5 h-3.5 text-[#E8400C] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                  <a href={`mailto:${member.email}`} className="hover:underline font-mono text-slate-500 hover:text-[#E8400C]">
                    {member.email}
                  </a>
                </div>
                <button
                  onClick={() => handleOpenDetails(member)}
                  className="w-full mt-4 bg-slate-50 text-slate-700 hover:bg-[#E8400C]/5 hover:text-[#E8400C] text-[10px] font-black uppercase py-2.5 px-4 rounded-xl border border-slate-100 hover:border-[#E8400C]/20 transition-all duration-150 text-center"
                >
                  View Full Profile
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-center">
          <svg className="w-8 h-8 text-slate-300 mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p className="text-xs text-slate-500 font-bold">No faculty members found matching your search.</p>
        </div>
      )}

      {/* Details Dialog Modal */}
      {selectedMember && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-white rounded-3xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col border border-border-dau shadow-2xl relative">
            {/* Modal Header */}
            <div className="p-6 border-b border-border-dau bg-slate-50/50 flex justify-between items-start gap-4">
              <div>
                <span className="text-[9px] font-black uppercase tracking-wider text-[#E8400C] block mb-1">
                  {selectedMember.designation}
                </span>
                <h2 className="text-base font-black text-slate-900 leading-tight">
                  {selectedMember.name}
                </h2>
              </div>
              <button
                onClick={() => setSelectedMember(null)}
                className="p-1 rounded-full hover:bg-slate-200 text-slate-400 hover:text-slate-700 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l18 18" />
                </svg>
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-4">
              {loadingDetails ? (
                <div className="space-y-4 animate-pulse">
                  <div className="h-4 bg-slate-100 rounded w-full" />
                  <div className="h-4 bg-slate-100 rounded w-5/6" />
                  <div className="h-4 bg-slate-100 rounded w-2/3" />
                </div>
              ) : (
                <div className="prose prose-slate max-w-none text-xs sm:text-sm text-slate-700 leading-relaxed">
                  <MarkdownRenderer content={detailContent} />
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-border-dau bg-slate-50/50 flex justify-end gap-3">
              <button
                onClick={() => setSelectedMember(null)}
                className="bg-slate-200 text-slate-700 text-[10px] font-black uppercase py-2 px-5 rounded-lg hover:bg-slate-300 transition-colors"
              >
                Close Profile
              </button>
              <a
                href={`mailto:${selectedMember.email}`}
                className="bg-[#E8400C] text-white text-[10px] font-black uppercase py-2 px-5 rounded-lg hover:bg-[#D7380A] transition-colors flex items-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                Send Email
              </a>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
