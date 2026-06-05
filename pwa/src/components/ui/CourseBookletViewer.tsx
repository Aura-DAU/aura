import React from "react";

interface CourseBookletViewerProps {
  pdfUrl?: string;
  title?: string;
  fileName?: string;
}

export default function CourseBookletViewer({
  pdfUrl = "/documents/Course_Booklet_for_Autumn_2025-26.pdf",
  title = "DAU Course Booklet Autumn 2025-26",
  fileName = "course_booklet_for_autumn_2025-26.pdf",
}: CourseBookletViewerProps) {
  return (
    <div className="flex-1 w-full h-full bg-slate-900 flex flex-col">
      {/* Premium Adobe-Style Dark PDF Reader Toolbar */}
      <div className="h-12 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-4 text-slate-200 shrink-0 select-none">
        {/* Left Side: Document Icon & Name */}
        <div className="flex items-center gap-2.5">
          <div className="bg-primary-dau text-white text-[8px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
            PDF
          </div>
          <span className="text-xs font-mono font-bold text-slate-300 tracking-tight">
            {fileName}
          </span>
        </div>
        
        {/* Right Side: Open Fullscreen Action */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => window.open(pdfUrl, "_blank")}
            type="button"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 hover:text-white text-[10px] font-black transition-colors"
            title="Open PDF in New Tab"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            <span>Open Fullscreen</span>
          </button>
        </div>
      </div>

      {/* Native Browser PDF Embed */}
      <div className="flex-1 w-full bg-slate-800 relative">
        <iframe
          src={pdfUrl}
          className="w-full h-full border-none absolute inset-0 bg-slate-800"
          title={title}
        />
      </div>
    </div>
  );
}
