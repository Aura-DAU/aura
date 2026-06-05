"use client";

import React, { useState, useEffect } from "react";
import MarkdownRenderer from "@/components/ui/MarkdownRenderer";
import { fetchStudentServiceDocument } from "@/services/studentServices";

const LEAVE_POLICY_FALLBACK = `### student leave policy
1. Students must apply for leaves in advance using the SIS portal.
2. For medical leaves exceeding 3 days, a certificate from the institute doctor is mandatory.
3. Total leaves in a semester cannot exceed 15 days to maintain the minimum 75% attendance threshold.
4. Out-of-station leave requires parental email verification.`;

export default function StudentServicesPage() {
  const [leaveContent, setLeaveContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"idcard" | "bonafide" | "leave" | "fees">("idcard");

  useEffect(() => {
    async function loadContent() {
      try {
        const res = await fetchStudentServiceDocument({ fileName: "student_leave_policy.md" });
        if (res.success && res.content) {
          setLeaveContent(res.content);
        } else {
          setLeaveContent(LEAVE_POLICY_FALLBACK);
        }
      } catch {
        setLeaveContent(LEAVE_POLICY_FALLBACK);
      } finally {
        setLoading(false);
      }
    }
    loadContent();
  }, []);

  const workflows = {
    idcard: {
      title: "Lost ID Card Replacement",
      steps: [
        { label: "File a Complaint", desc: "Report the lost card to the Security Office." },
        { label: "Pay Replacement Fee", desc: "Pay ₹500 at the Accounts Office and collect the fee receipt." },
        { label: "Submit Request Form", desc: "Fill out the ID Card Re-issue Form at the Student Services counter." },
        { label: "Collect New Card", desc: "New RFID card will be issued within 3 working days." },
      ],
      note: "Keep the payment receipt safe. A fine of ₹500 is charged for replacement.",
    },
    bonafide: {
      title: "Request Bonafide Certificate",
      steps: [
        { label: "Apply Online", desc: "Log in to the SIS/ERP portal and submit a Bonafide Request." },
        { label: "State Purpose", desc: "Specify if needed for Bank Account, Passport, Visa, or Education Loan." },
        { label: "Verification", desc: "Registry office will verify academic registration status." },
        { label: "Collect Certificate", desc: "Pick up the signed certificate from the Student Counter in 24 hours." },
      ],
      note: "No charge is levied for standard bonafide certificates.",
    },
    fees: {
      title: "Semester Fee Payment & No-Dues",
      steps: [
        { label: "View Fee Challan", desc: "Access the semester fee challan on the ERP portal under Student Accounts." },
        { label: "Online Transfer", desc: "Pay via NetBanking, NEFT, or Credit/Debit Card using the payment gateway." },
        { label: "Submit Receipt", desc: "Upload the transaction receipt if paying via manual NEFT/RTGS transfer." },
        { label: "Collect Clearance", desc: "No-Dues clearance is updated automatically within 24 hours of receipt." },
      ],
      note: "Late payments attract a fine of ₹100 per day after the registration deadline.",
    },
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Student Services & Administration
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Access interactive workflows for ID cards, bonafide requests, leave applications, and fee clearances.
        </p>
      </div>

      {/* Services Tabs Navigation */}
      <div className="flex border-b border-border-dau overflow-x-auto gap-2">
        <button
          onClick={() => setActiveTab("idcard")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "idcard"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Lost ID Card Workflow
        </button>
        <button
          onClick={() => setActiveTab("bonafide")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "bonafide"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Bonafide Certificate
        </button>
        <button
          onClick={() => setActiveTab("leave")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "leave"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Leave Policy
        </button>
        <button
          onClick={() => setActiveTab("fees")}
          className={`px-4 py-2 text-xs font-black uppercase tracking-wider border-b-2 transition-all duration-200 whitespace-nowrap ${
            activeTab === "fees"
              ? "border-[#E8400C] text-[#E8400C]"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Semester Fees
        </button>
      </div>

      {/* Tabs Content */}
      <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-8 shadow-sm">
        {activeTab === "leave" ? (
          <div>
            <h2 className="text-base font-bold text-foreground mb-4 border-l-4 border-[#E8400C] pl-3">
              Official Student Leave Guidelines
            </h2>
            {loading ? (
              <div className="space-y-3 animate-pulse">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
              </div>
            ) : (
              <div className="prose prose-slate max-w-none text-slate-700 text-xs sm:text-sm">
                <MarkdownRenderer content={leaveContent} />
              </div>
            )}
          </div>
        ) : (
          <div>
            {/* Standard workflow visualization */}
            {(() => {
              const flow = workflows[activeTab as keyof typeof workflows];
              if (!flow) return null;

              return (
                <div className="space-y-6">
                  <div>
                    <h2 className="text-base font-bold text-foreground mb-1.5 border-l-4 border-[#E8400C] pl-3">
                      {flow.title}
                    </h2>
                    <p className="text-xs text-text-muted">
                      Follow these sequential steps to complete your administrative request.
                    </p>
                  </div>

                  {/* Steps Timeline Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
                    {flow.steps.map((step, idx) => (
                      <div key={idx} className="relative bg-slate-50 border border-border-dau/60 rounded-2xl p-5 hover:shadow transition-all duration-200">
                        {/* Circle step number indicator */}
                        <div className="w-8 h-8 rounded-full bg-[#E8400C]/10 border border-[#E8400C]/25 text-[#E8400C] text-xs font-black flex items-center justify-center mb-3">
                          {idx + 1}
                        </div>
                        <h3 className="text-xs font-black text-slate-900 mb-1 leading-tight">
                          {step.label}
                        </h3>
                        <p className="text-[10px] text-slate-500 font-medium leading-relaxed">
                          {step.desc}
                        </p>
                      </div>
                    ))}
                  </div>

                  {/* Warning/Note footer */}
                  <div className="bg-orange-50 border border-orange-200/50 rounded-2xl p-4 flex gap-3 items-center">
                    <svg className="w-5 h-5 text-[#E8400C] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <p className="text-[10px] font-bold text-slate-700 leading-normal">
                      <strong className="text-[#E8400C] uppercase tracking-wide mr-1">Note:</strong> {flow.note}
                    </p>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </div>
    </div>
  );
}
