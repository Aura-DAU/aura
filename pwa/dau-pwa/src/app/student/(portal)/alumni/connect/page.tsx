"use client";

import React, { useState, useEffect } from "react";
import { fetchStudentServiceDocument } from "@/lib/api/studentServices.action";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";

const ID_CARD_FALLBACK = `### alumni id card application
1. Registered alumni can apply for a permanent campus entry ID card.
2. Submit graduation degree verification on the alumni registry portal.
3. Fee of ₹250 applies. Allows campus library and sports complexes access.`;

const DOC_SERVICE_FALLBACK = `### alumni document service
1. Alumni can request transcripts, duplicate certificates, and migration certifications online.
2. Processing time: 7-10 working days. Shipping charges apply for physical deliveries.`;

export default function AlumniConnectPage() {
  const [idContent, setIdContent] = useState("");
  const [docContent, setDocContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"mentorship" | "idcard" | "docs">("mentorship");

  useEffect(() => {
    async function loadData() {
      try {
        const [idRes, docRes] = await Promise.all([
          fetchStudentServiceDocument({ fileName: "alumni_id_card_application.md" }),
          fetchStudentServiceDocument({ fileName: "alumni_document_service.md" }),
        ]);

        if (idRes.success && idRes.content) {
          setIdContent(idRes.content);
        } else {
          setIdContent(ID_CARD_FALLBACK);
        }

        if (docRes.success && docRes.content) {
          setDocContent(docRes.content);
        } else {
          setDocContent(DOC_SERVICE_FALLBACK);
        }
      } catch {
        setIdContent(ID_CARD_FALLBACK);
        setDocContent(DOC_SERVICE_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Alumni Mentorship & Services
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Apply for alumni ID cards, request transcripts/documents, and join alumni-student mentorship circles.
        </p>
      </div>

      {/* Connection Tabs */}
      <div className="flex border-b border-border-dau overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab("mentorship")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "mentorship"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Mentorship Circles
        </button>
        <button
          onClick={() => setActiveTab("idcard")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "idcard"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Alumni ID Card
        </button>
        <button
          onClick={() => setActiveTab("docs")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "docs"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Alumni Document Service
        </button>
      </div>

      {/* Connection Contents */}
      <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
        {activeTab === "mentorship" && (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-foreground mb-1.5 border-l-4 border-[#E8400C] pl-3">
                Alumni-Student Mentoring Program
              </h2>
              <p className="text-xs text-text-muted">
                Connect with graduates working in senior engineering, product, consulting, and academic roles worldwide.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 space-y-4">
                <h3 className="text-xs font-black text-slate-900 uppercase tracking-wide">
                  Available Guidance areas
                </h3>
                <div className="space-y-2 text-xs font-medium text-slate-700">
                  <p><strong>Technical Mentoring:</strong> Code reviews, tech stack choices, system architectures.</p>
                  <p><strong>Career Coaching:</strong> Mock interviews, resume reviews, salary negotiations.</p>
                  <p><strong>Academic Pathways:</strong> PhD shortlists, research paper guidelines, scholarship applications.</p>
                </div>
              </div>

              <div className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 space-y-4 flex flex-col justify-between">
                <div>
                  <h3 className="text-xs font-black text-slate-900 uppercase tracking-wide mb-2">
                    How to Participate
                  </h3>
                  <p className="text-xs text-slate-600 font-medium leading-relaxed">
                    Student applications open at the start of each semester. Submit your career interests and resume to get matched with an alumnus mentor.
                  </p>
                </div>
                <a
                  href="#"
                  className="bg-[#E8400C] text-white text-[10px] font-black uppercase py-2.5 px-6 rounded-xl shadow-md shadow-[#E8400C]/20 transition-all duration-150 inline-block text-center mt-4 w-full"
                >
                  Join Mentorship Circle
                </a>
              </div>
            </div>
          </div>
        )}

        {activeTab === "idcard" && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
              Alumni ID Card Application
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={idContent} />
              </div>
            )}
          </div>
        )}

        {activeTab === "docs" && (
          <div className="space-y-4">
            <h2 className="text-base font-bold text-foreground border-l-4 border-[#E8400C] pl-3">
              Official Alumni Document & Registry Services
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={docContent} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
