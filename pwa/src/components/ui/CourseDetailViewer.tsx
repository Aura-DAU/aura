import React from "react";
import { CourseMetadata } from "@/lib/utils/courseParser";
import MarkdownRenderer from "./MarkdownRenderer";

interface CourseDetailViewerProps {
  course: CourseMetadata;
  content: string;
  loading: boolean;
  viewingOriginalPdf: boolean;
  onToggleViewMode: () => void;
  zoom: number;
  onZoomIn: () => void;
  onZoomOut: () => void;
  onZoomReset: () => void;
  fitWidth: boolean;
  onToggleFitWidth: () => void;
}

export default function CourseDetailViewer({
  course,
  content,
  loading,
  viewingOriginalPdf,
  onToggleViewMode,
  zoom,
  onZoomIn,
  onZoomOut,
  onZoomReset,
  fitWidth,
  onToggleFitWidth,
}: CourseDetailViewerProps) {
  return (
    <>
      <style>{`
        @media print {
          body {
            background-color: white !important;
            color: black !important;
          }
          div:not(#printable-pdf-document), 
          main, 
          aside, 
          nav, 
          button, 
          header {
            display: none !important;
          }
          #printable-pdf-document {
            display: block !important;
            position: absolute;
            left: 0;
            top: 0;
            width: 100% !important;
            max-width: 100% !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
          }
        }
      `}</style>

      {/* Premium Adobe-Style Dark PDF Reader Toolbar */}
      <div className="h-12 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-4 text-slate-200 shrink-0 select-none">
        <div className="flex items-center gap-2.5">
          <div className="bg-primary-dau text-white text-[8px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
            PDF
          </div>
          <span className="text-xs font-mono font-bold text-slate-300 tracking-tight max-w-[150px] sm:max-w-xs truncate">
            {viewingOriginalPdf && course.pdfPath
              ? course.pdfPath.split("/").pop()
              : `${course.code.toLowerCase()}_syllabus_policy.pdf`}
          </span>
        </div>

        <div className="flex items-center gap-3">
          {course.pdfPath && (
            <button
              onClick={onToggleViewMode}
              type="button"
              className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 border border-slate-600 hover:border-slate-500 text-[9px] font-black uppercase tracking-wider text-white transition-all duration-200"
            >
              {viewingOriginalPdf ? (
                <>
                  <svg className="w-3.5 h-3.5 text-orange-450" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span>Interactive Text</span>
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5 text-red-450" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <span>Original PDF</span>
                </>
              )}
            </button>
          )}

          {(!course.pdfPath || !viewingOriginalPdf) && (
            <>
              <button
                onClick={onZoomOut}
                type="button"
                className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                title="Zoom Out"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M20 12H4" />
                </svg>
              </button>
              
              <button 
                onClick={onZoomReset}
                type="button"
                className="text-[10px] font-mono font-black tracking-wider bg-slate-900 px-2 py-0.5 rounded border border-slate-700 text-slate-300 hover:text-white"
                title="Reset Zoom"
              >
                {zoom}%
              </button>

              <button
                onClick={onZoomIn}
                type="button"
                className="p-1 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                title="Zoom In"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
                </svg>
              </button>

              <div className="h-4 w-px bg-slate-700 mx-1 hidden sm:block" />

              <button
                onClick={onToggleFitWidth}
                type="button"
                className={`p-1 rounded hover:bg-slate-700 transition-colors hidden sm:block ${
                  fitWidth ? "text-primary-dau" : "text-slate-400 hover:text-slate-100"
                }`}
                title="Fit to Width"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 8V4m0 0h4M4 4l5 5m11-5V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l-5-5m11 5v-4m0 4h-4m4 0l-5-5" />
                </svg>
              </button>
            </>
          )}
        </div>

        <div className="flex items-center gap-2">
          {viewingOriginalPdf && course.pdfPath ? (
            <button
              onClick={() => window.open(course.pdfPath, "_blank")}
              type="button"
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 hover:text-white text-[10px] font-black transition-colors"
              title="Open PDF in New Tab"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              <span className="hidden sm:inline">Fullscreen</span>
            </button>
          ) : (
            <>
              <button
                onClick={() => window.print()}
                type="button"
                className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                title="Print Specification"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
              </button>

              <button
                onClick={() => window.open(course.filePath, "_blank")}
                type="button"
                className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                title="Open Source Markdown"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                </svg>
              </button>
            </>
          )}
        </div>
      </div>

      {/* Canvas Frame */}
      <div className="flex-1 overflow-y-auto p-6 bg-slate-800 scrollbar-thin scrollbar-thumb-slate-700 relative">
        {viewingOriginalPdf && course.pdfPath ? (
          <iframe
            src={course.pdfPath}
            className="w-full h-full border-none absolute inset-0 bg-slate-800"
            title={`${course.code} Original PDF`}
          />
        ) : loading ? (
          <div className="space-y-6 animate-pulse max-w-[760px] mx-auto bg-white border border-slate-200 rounded p-8 sm:p-12 min-h-[800px]">
            <div className="h-7 bg-slate-100 rounded w-1/3" />
            <div className="space-y-2">
              <div className="h-4 bg-slate-100 rounded w-full" />
              <div className="h-4 bg-slate-100 rounded w-5/6" />
              <div className="h-4 bg-slate-100 rounded w-4/5" />
            </div>
            <div className="h-6 bg-slate-100 rounded w-1/4 mt-8" />
            <div className="h-24 bg-slate-50 rounded border border-slate-100 w-full" />
          </div>
        ) : (
          /* Simulated A4 Sheet */
          <div
            id="printable-pdf-document"
            className="mx-auto bg-white border border-slate-900/10 shadow-2xl p-8 sm:p-14 relative min-h-[1050px] transition-all duration-200 select-text"
            style={{
              width: fitWidth ? "100%" : `${720 * (zoom / 100)}px`,
              fontFamily: "Georgia, serif",
            }}
          >
            <div className="border-b border-slate-200 pb-3.5 mb-10 flex justify-between items-center text-[9px] text-slate-400 font-bold uppercase tracking-widest select-none">
              <span className="text-primary-dau tracking-wide">Dhirubhai Ambani University</span>
              <span>Course Policy Outline Specification</span>
            </div>

            <div className="prose prose-slate max-w-none text-slate-800 text-[13px] leading-relaxed">
              <MarkdownRenderer content={content} />
            </div>

            <div className="mt-14 pt-3.5 border-t border-slate-100 flex justify-between items-center text-[8px] text-slate-400 font-bold uppercase tracking-widest select-none">
              <span>DAU Academic Registry &copy; {new Date().getFullYear()}</span>
              <span>Official Copy (1 / 1 Pages)</span>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
