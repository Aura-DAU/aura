"use client";

import React, { useState, useEffect } from "react";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";
import { fetchStudentServiceDocument } from "@/lib/api/studentServices.action";

const MOCK_EXAM_CONTENT = `### official rules
Rules and regulations governing semesters, mid-semesters, end-semesters, and evaluation rubrics at Dhirubhai Ambani University.

- **Passing Standard:** Minimum 40% aggregate or specific letter grade requirements in each course block.
- **Attendance Requirement:** Minimum 75% attendance is mandatory to appear in end-semester final exams.
- **Grading Scale:** Relative grading scheme with grades ranging from F (Fail) to CPI index 10.0.

### downloadable resources
- [Examination Rules for Students](https://daiict.ac.in/sites/default/files/other-files/Examination_Rules_for_Students.pdf)
- [Rules & Guidelines for Conducting written examination for Person with Benchmark Disabilities](https://daiict.ac.in/sites/default/files/other-files/Rules_and_Guidelines_for_Conducting_written_examination_for_Person_with_Benchmark_Disabilities.pdf)
- [Guidelines of Exams Malpractices](https://daiict.ac.in/sites/default/files/other-files/Guidelines_of_Exams_Malpractices.pdf)`;

export default function ExaminationsPage() {
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadContent() {
      try {
        const res = await fetchStudentServiceDocument({ fileName: "examination_rules.md" });
        if (res.success && res.content) {
          setContent(res.content);
        } else {
          setContent(MOCK_EXAM_CONTENT);
        }
      } catch {
        setContent(MOCK_EXAM_CONTENT);
      } finally {
        setLoading(false);
      }
    }
    loadContent();
  }, []);

  const examResources = [
    {
      title: "Examination Rules for Students",
      desc: "Standard rules, grades mapping, evaluation parameters, and re-evaluation guidelines.",
      pdfUrl: "https://daiict.ac.in/sites/default/files/other-files/Examination_Rules_for_Students.pdf",
    },
    {
      title: "Guidelines for Benchmark Disabilities",
      desc: "Accommodations, extra hours rules, and scribe specifications for candidates with benchmark disabilities.",
      pdfUrl: "https://daiict.ac.in/sites/default/files/other-files/Rules_and_Guidelines_for_Conducting_written_examination_for_Person_with_Benchmark_Disabilities.pdf",
    },
    {
      title: "Guidelines of Exams Malpractices",
      desc: "Codes of conduct, prohibited activities in examination blocks, and DAC penalties.",
      pdfUrl: "https://daiict.ac.in/sites/default/files/other-files/Guidelines_of_Exams_Malpractices.pdf",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Examinations Rules & Regulations
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Review official evaluation policies, disability accommodation guides, and malpractice definitions.
        </p>
      </div>

      {/* Grid containing description and links */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Interactive content list */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              Overview & Regulations
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
                <div className="h-4 bg-slate-100 rounded w-4/5" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-xs sm:text-sm leading-relaxed text-slate-700">
                <MarkdownRenderer content={content} />
              </div>
            )}
          </div>
        </div>

        {/* Right: Quick PDF Resources Cards */}
        <div className="space-y-4">
          <div className="bg-slate-50 border border-border-dau rounded-3xl p-6">
            <h2 className="text-sm font-black text-slate-800 uppercase tracking-wider mb-4">
              Official PDF Documents
            </h2>
            <div className="space-y-4">
              {examResources.map((res, idx) => (
                <div
                  key={idx}
                  className="bg-white border border-border-dau rounded-2xl p-4 hover:shadow-md transition-all duration-200"
                >
                  <h3 className="text-xs font-black text-slate-900 mb-1 leading-tight">
                    {res.title}
                  </h3>
                  <p className="text-[10px] text-slate-500 font-medium leading-relaxed mb-3">
                    {res.desc}
                  </p>
                  <a
                    href={res.pdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-[10px] font-black text-[#E8400C] hover:underline"
                  >
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download PDF Document
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
