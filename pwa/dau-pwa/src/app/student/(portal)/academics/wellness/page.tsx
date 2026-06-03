"use client";

import React, { useState, useEffect } from "react";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";
import { fetchStudentServiceDocument } from "@/lib/api/studentServices.action";

const RAGGING_FALLBACK = `### anti-ragging policy
1. Ragging in any form is strictly prohibited on campus.
2. Any student found guilty of ragging is liable for severe disciplinary action including expulsion from the university.
3. Incidents must be reported immediately to the Anti-Ragging Vigilance Committee.`;

export default function WellnessPage() {
  const [raggingContent, setRaggingContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"counseling" | "anti-ragging" | "emergency">("counseling");

  useEffect(() => {
    async function loadContent() {
      try {
        const res = await fetchStudentServiceDocument({ fileName: "curbing_ragging.md" });
        if (res.success && res.content) {
          setRaggingContent(res.content);
        } else {
          setRaggingContent(RAGGING_FALLBACK);
        }
      } catch {
        setRaggingContent(RAGGING_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadContent();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Wellness & Counseling
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Access anti-ragging support, mental health counseling services, student grievance cells, and anonymous hotlines.
        </p>
      </div>

      {/* Wellness Tabs */}
      <div className="flex border-b border-border-dau overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab("counseling")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "counseling"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Mental Health & Counseling
        </button>
        <button
          onClick={() => setActiveTab("anti-ragging")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "anti-ragging"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Anti-Ragging Support
        </button>
        <button
          onClick={() => setActiveTab("emergency")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "emergency"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Anonymous Helpline
        </button>
      </div>

      {/* Wellness Tab Content */}
      <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
        {activeTab === "counseling" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-foreground mb-1.5 border-l-4 border-[#E8400C] pl-3">
                University Counseling Cell
              </h2>
              <p className="text-xs text-text-muted">
                Dhirubhai Ambani University provides confidential mental health and psychological counseling services to all students free of charge.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 space-y-4">
                <h3 className="text-xs font-black text-slate-900 uppercase tracking-wide">
                  Appointment Details
                </h3>
                <div className="space-y-2 text-xs font-medium text-slate-700">
                  <p><strong>Timings:</strong> 10:00 AM - 05:30 PM (Mon - Fri)</p>
                  <p><strong>Location:</strong> Room 102, Student Activity Block (SAB)</p>
                  <p><strong>Counselor:</strong> Dr. Shalini Shah (Resident Psychologist)</p>
                </div>
              </div>

              <div className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 space-y-4">
                <h3 className="text-xs font-black text-slate-900 uppercase tracking-wide">
                  How to book
                </h3>
                <p className="text-xs text-slate-600 font-medium leading-relaxed">
                  Send an email to <a href="mailto:counseling@dau.ac.in" className="text-[#E8400C] hover:underline font-bold">counseling@dau.ac.in</a> to schedule an in-person or online session. Walk-ins are welcome for urgent/crisis situations.
                </p>
              </div>
            </div>
          </div>
        )}

        {activeTab === "anti-ragging" && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
              Curbing the Menace of Ragging
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={raggingContent} />
              </div>
            )}
          </div>
        )}

        {activeTab === "emergency" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-foreground mb-1.5 border-l-4 border-[#E8400C] pl-3">
                Anonymous Student Helpline
              </h2>
              <p className="text-xs text-text-muted">
                If you or anyone you know is facing harassment, discrimination, or mental distress, report anonymously or seek advice using the hotlines below.
              </p>
            </div>

            <div className="bg-orange-50 border border-orange-200/50 rounded-2xl p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[9px] font-black uppercase text-[#E8400C] tracking-wide">
                  National Anti-Ragging Call Center
                </span>
                <h3 className="text-lg font-black text-slate-900 font-mono">
                  1800-180-5522
                </h3>
                <p className="text-[10px] text-slate-500 font-medium">
                  24/7 toll-free helpline. Complies with UGC guidelines.
                </p>
              </div>
              <a
                href="mailto:helpline@antiragging.in"
                className="bg-[#E8400C] text-white text-xs font-black uppercase py-3 px-6 rounded-xl hover:bg-[#D7380A] shadow-md shadow-[#E8400C]/20 transition-all duration-150 text-center"
              >
                Email National Helpline
              </a>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
