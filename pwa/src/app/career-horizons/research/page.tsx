"use client";

import React, { useState, useEffect } from "react";
import { fetchStudentServiceDocument } from "@/services/studentServices";
import MarkdownRenderer from "@/components/ui/MarkdownRenderer";

const ECELL_FALLBACK = `### incubation cell
- **Mentor:** Prof. Manish K. Gupta
- **Incubated Startups:** 10+ student-led ventures.
- **Resources:** Seed funding, co-working space, IP filing support.`;

export default function ResearchInnovationPage() {
  const [ecellContent, setEcellContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"labs" | "incubation">("labs");

  useEffect(() => {
    async function loadContent() {
      try {
        const res = await fetchStudentServiceDocument({ fileName: "entrepreneurship_cell.md" });
        if (res.success && res.content) {
          setEcellContent(res.content);
        } else {
          setEcellContent(ECELL_FALLBACK);
        }
      } catch {
        setEcellContent(ECELL_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadContent();
  }, []);

  const researchLabs = [
    { name: "Speech Processing Lab", area: "Automatic Speech Recognition, Text-to-Speech synthesis, speaker verification.", head: "Dr. Hemant Patil" },
    { name: "VLSI Design & Hardware Security Lab", area: "RTL to GDS-II flows, memory architectures, crypto accelerators.", head: "Dr. Tapas Maiti" },
    { name: "AI & Cognitive Modeling Lab", area: "Deep learning models, natural language processing, computer vision networks.", head: "Dr. Sourish Dasgupta" },
    { name: "Intelligent UX (IUxD) Design Lab", area: "Immersive interfaces, human-computer interactions, usability testing.", head: "Prof. Sanjay Chaudhary" },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Research & Innovation Ecosystem
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Explore research labs, funded projects, incubation wings, and startup ecosystems on campus.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border-dau overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab("labs")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "labs"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Research Labs & Groups
        </button>
        <button
          onClick={() => setActiveTab("incubation")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "incubation"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Incubation Cell & Startups
        </button>
      </div>

      {/* Tab Contents */}
      <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
        {activeTab === "labs" ? (
          <div className="space-y-6">
            <div>
              <h2 className="text-base font-bold text-foreground mb-1.5 border-l-4 border-[#E8400C] pl-3">
                Active Research Laboratories
              </h2>
              <p className="text-xs text-text-muted">
                Dhirubhai Ambani University houses specialized research units supporting undergraduate, postgraduate, and PhD scholars.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {researchLabs.map((lab, idx) => (
                <div key={idx} className="bg-slate-50 border border-border-dau/60 rounded-2xl p-5 hover:shadow transition-all duration-200">
                  <h3 className="text-xs font-black text-slate-900 mb-1 leading-tight">
                    {lab.name}
                  </h3>
                  <p className="text-[9px] font-black uppercase text-[#E8400C] bg-orange-50 border border-orange-200/50 px-1.5 py-0.5 rounded inline-block mt-1">
                    PI: {lab.head}
                  </p>
                  <p className="text-[10px] text-slate-500 font-medium leading-relaxed mt-3">
                    <strong className="text-slate-800 font-bold block mb-0.5">Focus Areas:</strong>
                    {lab.area}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div>
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              DAU Incubation & Entrepreneurship Center
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={ecellContent} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
