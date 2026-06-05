"use client";

import React, { useState, useEffect } from "react";
import MarkdownRenderer from "@/components/ui/MarkdownRenderer";
import { fetchStudentServiceDocument } from "@/services/studentServices";

const HOSTEL_RULES_CONTENT = `### room allocation
1. The allotment of rooms for new students will be done by the Wardens.
2. No requests for a change of rooms will be entertained.
3. The Dean of Students, Wardens, and Hostel Supervisors reserve the right to allot/re-allot and withdraw the accommodation provided.
4. The allotment will only be made to a registered student of DA-IICT.
5. The resident has to vacate the room within five days of his/her ceasing to be a student of DA-IICT.
6. A UG student will be allotted a room only for the first four years of stay on campus.
7. Hostellers must give complete contact details of at least two guardians/relatives.

### behavior and discipline
1. Residents must ensure peace and tranquility within the Halls of Residence area.
2. Residents will behave according to social ethics and respect the privacy of others.
3. **Consumption or possession of alcoholic drinks**, usage of any form of intoxicating materials are **strictly prohibited**.
4. The entire campus of DA-IICT is a **no-smoking zone**.
5. All residents must return to the campus by **midnight 12 AM**.
6. No resident student will be allowed outside the campus from **midnight till 6 AM**.
7. Ragging is a criminal offence and strictly prohibited.
8. A minimum fine of **₹1,000/- per day** would be charged if anyone else stays in a resident's room without permission.
9. **Residents cannot bring food inside the Halls of Residence.** Fine of ₹1,000.
10. High power-consuming electrical equipment is strictly prohibited: irons, heaters, ovens, kettles.

### vehicles
1. Students are **NOT allowed to keep 4-wheelers** on campus.
2. Students can keep **2-wheelers** (bicycles, scooters, motorcycles) - maximum 1.
3. Parking must be in authorized areas only. Speed limits and helmets are mandatory.

### maintenance
1. Residents are responsible for keeping rooms clean.
2. Spot checks of rooms can be made without prior notice.

### visitors
1. Visitors are **NOT allowed** into the Halls of Residence Complex.
2. Guest Room available for medical emergencies: ₹200 (DA-IICT student), ₹250 (outsider/parents) per day.

### security
1. Keep belongings under lock and key. Lock room before leaving.
2. Loss of key: fine of ₹500/- plus lock cost.
3. **Residents are not allowed to use their own locks.**`;

export default function HostelRulesPage() {
  const [zoom, setZoom] = useState(100);
  const [fitWidth, setFitWidth] = useState(false);
  const [rulesContent, setRulesContent] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadContent() {
      try {
        const res = await fetchStudentServiceDocument({ fileName: "hostel_rules_and_regulations.md" });
        if (res.success && res.content) {
          setRulesContent(res.content);
        } else {
          setRulesContent(HOSTEL_RULES_CONTENT);
        }
      } catch {
        setRulesContent(HOSTEL_RULES_CONTENT);
      } finally {
        setLoading(false);
      }
    }
    loadContent();
  }, []);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 10, 50));
  const handleZoomReset = () => setZoom(100);

  return (
    <div className="space-y-6">
      {/* Dynamic CSS for beautiful PDF-like printing */}
      <style>{`
        @media print {
          body {
            background-color: white !important;
            color: black !important;
          }
          div:not(#printable-hostel-pdf), 
          main, 
          aside, 
          nav, 
          button, 
          header {
            display: none !important;
          }
          #printable-hostel-pdf {
            display: block !important;
            position: absolute;
            left: 0;
            top: 0;
            width: 100% !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
          }
        }
      `}</style>

      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Hostel Rules & Regulations
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Official guidelines governing room allocations, curfew rules, visitor policies, and code of conduct in the Halls of Residence.
        </p>
      </div>

      {/* Adobe-Style PDF Viewer Wrapper */}
      <div className="flex flex-col h-[calc(100vh-210px)] min-h-[500px] overflow-hidden bg-slate-900 rounded-[24px] border border-slate-800 shadow-xl">
        {/* PDF Reader Toolbar */}
        <div className="h-12 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-4 text-slate-200 shrink-0 select-none">
          <div className="flex items-center gap-2.5">
            <div className="bg-[#E8400C] text-white text-[8px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
              PDF
            </div>
            <span className="text-xs font-mono font-bold text-slate-300 tracking-tight max-w-[150px] sm:max-w-xs truncate">
              hostel-rules-and-regulations.pdf
            </span>
          </div>

          {/* Zoom controls */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleZoomOut}
              className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
              title="Zoom Out"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
              </svg>
            </button>
            <button
              onClick={handleZoomReset}
              className="text-[10px] font-mono font-black tracking-wider bg-slate-900 px-2 py-0.5 rounded border border-slate-700 text-slate-300 hover:text-white"
              title="Reset Zoom"
            >
              {zoom}%
            </button>
            <button
              onClick={handleZoomIn}
              className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
              title="Zoom In"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
            </button>

            <div className="h-4 w-px bg-slate-700 mx-1 hidden sm:block" />

            <button
              onClick={() => setFitWidth(!fitWidth)}
              className={`p-1 rounded hover:bg-slate-700 transition-colors hidden sm:block ${
                fitWidth ? "text-[#E8400C]" : "text-slate-400 hover:text-slate-100"
              }`}
              title="Fit to Width"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-5V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5" />
              </svg>
            </button>
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2">
            <button
              onClick={() => window.print()}
              className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
              title="Print Rules"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Page body canvas */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-800 scrollbar-thin scrollbar-thumb-slate-700">
          {loading ? (
            <div className="space-y-6 animate-pulse max-w-[760px] mx-auto bg-white border border-slate-200 rounded p-8 sm:p-12 min-h-[800px]">
              <div className="h-7 bg-slate-100 rounded w-1/3" />
              <div className="space-y-2">
                <div className="h-4 bg-slate-100 rounded w-full" />
                <div className="h-4 bg-slate-100 rounded w-5/6" />
                <div className="h-4 bg-slate-100 rounded w-4/5" />
              </div>
            </div>
          ) : (
            <div
              id="printable-hostel-pdf"
              className="mx-auto bg-white border border-slate-900/10 shadow-2xl p-8 sm:p-14 relative min-h-[1000px] transition-all duration-200 select-text"
              style={{
                width: fitWidth ? "100%" : `${720 * (zoom / 100)}px`,
                fontFamily: "Georgia, serif",
              }}
            >
              {/* Elegant Watermark Header */}
              <div className="border-b border-slate-200 pb-3.5 mb-10 flex justify-between items-center text-[9px] text-slate-400 font-bold uppercase tracking-widest select-none">
                <span className="text-[#E8400C] tracking-wide">Dhirubhai Ambani University</span>
                <span>Halls of Residence Rules</span>
              </div>

              {/* Rules Body */}
              <div className="prose prose-slate max-w-none text-slate-800 text-[13px] leading-relaxed">
                <MarkdownRenderer content={rulesContent} />
              </div>

              {/* Watermark Footer */}
              <div className="mt-14 pt-3.5 border-t border-slate-100 flex justify-between items-center text-[8px] text-slate-400 font-bold uppercase tracking-widest select-none">
                <span>HMC Hostel Regulations Division &copy; {new Date().getFullYear()}</span>
                <span>Official PDF Copy</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
