"use client";

import React, { useState, useEffect } from "react";
import { CourseMetadata } from "@/lib/utils/courseParser";
import { fetchCourseContent } from "@/lib/api/courses.action";
import MarkdownRenderer from "./MarkdownRenderer";

interface CoursesInteractiveLayoutProps {
  initialCourses: CourseMetadata[];
}

export default function CoursesInteractiveLayout({
  initialCourses,
}: CoursesInteractiveLayoutProps) {
  const [courses] = useState<CourseMetadata[]>(initialCourses);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTerm, setSelectedTerm] = useState("All");
  
  // Selection & Details state
  const [selectedCourse, setSelectedCourse] = useState<CourseMetadata | null>(null);
  const [courseContent, setCourseContent] = useState<string>("");
  const [loadingContent, setLoadingContent] = useState(false);
  const [viewingFullBooklet, setViewingFullBooklet] = useState(true); // Default to full booklet PDF for stunning initial impact!
  const [viewingOriginalPdf, setViewingOriginalPdf] = useState(true); // Default to original PDF layout for direct genuine view!

  // Filter lists based on inputs
  const filteredCourses = courses.filter((course) => {
    const matchesSearch =
      course.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      course.code.toLowerCase().includes(searchQuery.toLowerCase());
      
    const matchesTerm =
      selectedTerm === "All" || course.term === selectedTerm;

    return matchesSearch && matchesTerm;
  });

  const handleSelectCourse = async (course: CourseMetadata) => {
    setViewingFullBooklet(false);
    setSelectedCourse(course);
    setViewingOriginalPdf(true);
    setLoadingContent(true);
    try {
      const response = await fetchCourseContent({ fileName: course.fileName });
      if (response.success) {
        setCourseContent(response.content);
      } else {
        setCourseContent("Failed to load course details.");
      }
    } catch (err) {
      console.error(err);
      setCourseContent("An error occurred while fetching course policy.");
    } finally {
      setLoadingContent(false);
    }
  };

  // Automatically select first course on desktop if none selected
  useEffect(() => {
    if (!viewingFullBooklet && filteredCourses.length > 0 && !selectedCourse && window.innerWidth >= 768) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      handleSelectCourse(filteredCourses[0]);
    }
  }, [filteredCourses, selectedCourse, viewingFullBooklet]);

  // Extract unique terms for filter pills
  const terms = ["All", ...Array.from(new Set(courses.map((c) => c.term)))];

  // PDF Viewer Simulation states
  const [zoom, setZoom] = useState(100);
  const [fitWidth, setFitWidth] = useState(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 10, 50));
  const handleZoomReset = () => setZoom(100);

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-210px)] min-h-[500px]">
      {/* Master List Pane (Left, 4 Cols) */}
      <div className="md:col-span-4 flex flex-col bg-white border border-[#E2E8F0] rounded-[24px] overflow-hidden h-full shadow-sm">
        {/* Search and Filters Header */}
        <div className="p-4 border-b border-[#E2E8F0] bg-slate-50/50 space-y-3">
          {/* Search bar */}
          <div className="relative">
            <svg
              className="absolute left-3.5 top-3 w-4 h-4 text-slate-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
            <input
              type="text"
              placeholder="Search code or title..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-white border border-[#E2E8F0] rounded-[16px] pl-10 pr-4 py-2.5 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-[#E8400C] focus:ring-1 focus:ring-[#E8400C]/20 transition-all duration-200"
            />
          </div>

          {/* Term Filter Pills */}
          <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
            {terms.map((term) => (
              <button
                key={term}
                onClick={() => setSelectedTerm(term)}
                className={`px-3 py-1.5 rounded-full text-[10px] font-black tracking-wider uppercase whitespace-nowrap transition-all duration-200 ${
                  selectedTerm === term
                    ? "bg-[#E8400C] text-white shadow-md shadow-[#E8400C]/15"
                    : "bg-slate-100 text-slate-500 hover:text-slate-900 hover:bg-slate-200"
                }`}
              >
                {term}
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable Course Cards list */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {/* View Merged PDF Booklet CTA */}
          <button
            onClick={() => {
              setViewingFullBooklet(true);
              setSelectedCourse(null);
            }}
            className={`w-full text-left p-4 rounded-[16px] transition-all duration-200 border flex items-center justify-between gap-3 ${
              viewingFullBooklet
                ? "bg-orange-50/80 border-orange-200 text-[#E8400C] shadow-sm font-bold border-l-4 border-l-[#E8400C] pl-3.5"
                : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700 hover:border-slate-300"
            }`}
          >
            <div className="flex items-center gap-2.5">
              <div className="bg-[#E8400C] text-white text-[9px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
                PDF
              </div>
              <div className="flex flex-col">
                <span className={`text-xs font-black ${viewingFullBooklet ? "text-[#E8400C]" : "text-slate-900"}`}>
                  Full Course Booklet
                </span>
                <span className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">
                  Official Merged PDF • 331 Pages
                </span>
              </div>
            </div>
            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <div className="h-px bg-[#E2E8F0] my-2" />

          {filteredCourses.length > 0 ? (
            filteredCourses.map((course) => {
              const isSelected = selectedCourse?.id === course.id;

              return (
                <button
                  key={course.id}
                  onClick={() => handleSelectCourse(course)}
                  className={`w-full text-left p-4 rounded-[16px] transition-all duration-200 border ${
                    isSelected
                      ? "bg-orange-50/80 border-orange-200 text-[#E8400C] shadow-sm font-bold border-l-4 border-l-[#E8400C] pl-3.5"
                      : "bg-white border-transparent hover:bg-slate-50 hover:border-slate-100 text-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-black ${
                        isSelected
                          ? "bg-[#E8400C] text-white"
                          : "bg-orange-50 text-[#E8400C] border border-orange-100"
                      }`}
                    >
                      {course.code}
                    </span>
                    <span className="text-[9px] font-black tracking-wide uppercase text-slate-400">
                      {course.term}
                    </span>
                  </div>
                  <h3 className={`text-xs font-black line-clamp-1 ${
                    isSelected ? "text-[#E8400C]" : "text-slate-900"
                  }`}>
                    {course.title}
                  </h3>
                </button>
              );
            })
          ) : (
            <div className="flex flex-col items-center justify-center h-48 text-center p-4">
              <svg
                className="w-8 h-8 text-slate-300 mb-2"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <p className="text-xs text-slate-500 font-bold">No courses found</p>
            </div>
          )}
        </div>
      </div>

      {/* Detail Pane (Right, 8 Cols) */}
      <div className="md:col-span-8 flex flex-col h-full overflow-hidden bg-slate-900 rounded-[24px] border border-slate-800 shadow-xl">
        {viewingFullBooklet ? (
          <div className="flex-1 w-full h-full bg-slate-900 flex flex-col">
            {/* Premium Adobe-Style Dark PDF Reader Toolbar */}
            <div className="h-12 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-4 text-slate-200 shrink-0 select-none">
              {/* Left Side: Document Icon & Name */}
              <div className="flex items-center gap-2.5">
                <div className="bg-[#E8400C] text-white text-[8px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
                  PDF
                </div>
                <span className="text-xs font-mono font-bold text-slate-300 tracking-tight">
                  course_booklet_for_autumn_2025-26.pdf
                </span>
              </div>
              
              {/* Right Side: Open Fullscreen Action */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => window.open("/documents/Course_Booklet_for_Autumn_2025-26.pdf", "_blank")}
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
                src="/documents/Course_Booklet_for_Autumn_2025-26.pdf"
                className="w-full h-full border-none absolute inset-0 bg-slate-800"
                title="DAU Course Booklet Autumn 2025-26"
              />
            </div>
          </div>
        ) : selectedCourse ? (
          <>
            {/* Dynamic CSS for beautiful PDF-like printing */}
            <style>{`
              @media print {
                body {
                  background-color: white !important;
                  color: black !important;
                }
                /* Hide everything in layout except the specific PDF content sheet */
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
            `}</style>            {/* Premium Adobe-Style Dark PDF Reader Toolbar */}
            <div className="h-12 bg-slate-800 border-b border-slate-700 flex items-center justify-between px-4 text-slate-200 shrink-0 select-none">
              {/* Left Side: Document Icon & Name */}
              <div className="flex items-center gap-2.5">
                <div className="bg-[#E8400C] text-white text-[8px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
                  PDF
                </div>
                <span className="text-xs font-mono font-bold text-slate-300 tracking-tight max-w-[150px] sm:max-w-xs truncate">
                  {viewingOriginalPdf && selectedCourse.pdfPath
                    ? selectedCourse.pdfPath.split("/").pop()
                    : `${selectedCourse.code.toLowerCase()}_syllabus_policy.pdf`}
                </span>
              </div>

              {/* Middle Section: Zoom & Toggle Controls */}
              <div className="flex items-center gap-3">
                {selectedCourse.pdfPath && (
                  <button
                    onClick={() => setViewingOriginalPdf(!viewingOriginalPdf)}
                    className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-slate-700 hover:bg-slate-600 border border-slate-600 hover:border-slate-500 text-[9px] font-black uppercase tracking-wider text-white transition-all duration-200"
                  >
                    {viewingOriginalPdf ? (
                      <>
                        <svg className="w-3.5 h-3.5 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <span>Interactive Text</span>
                      </>
                    ) : (
                      <>
                        <svg className="w-3.5 h-3.5 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                        </svg>
                        <span>Original PDF</span>
                      </>
                    )}
                  </button>
                )}

                {/* Show zoom controls only in interactive mode */}
                {(!selectedCourse.pdfPath || !viewingOriginalPdf) && (
                  <>
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

              {/* Right Side: Print & View Actions */}
              <div className="flex items-center gap-2">
                {viewingOriginalPdf && selectedCourse.pdfPath ? (
                  <button
                    onClick={() => window.open(selectedCourse.pdfPath, "_blank")}
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
                      className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                      title="Print Specification"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                      </svg>
                    </button>

                    <button
                      onClick={() => window.open(selectedCourse.filePath, "_blank")}
                      className="p-1.5 rounded hover:bg-slate-700 text-slate-400 hover:text-slate-100 transition-colors"
                      title="Open Source Markdown"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </button>
                  </>
                )}
              </div >
            </div>

            {/* Document Canvas Frame (Simulates dark gray workspace background) */}
            <div className="flex-1 overflow-y-auto p-6 bg-slate-800 scrollbar-thin scrollbar-thumb-slate-700 relative">
              {viewingOriginalPdf && selectedCourse.pdfPath ? (
                <iframe
                  src={selectedCourse.pdfPath}
                  className="w-full h-full border-none absolute inset-0 bg-slate-800"
                  title={`${selectedCourse.code} Original PDF`}
                />
              ) : loadingContent ? (
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
                /* High-fidelity simulated A4 PDF Page Sheet */
                <div
                  id="printable-pdf-document"
                  className="mx-auto bg-white border border-slate-900/10 shadow-2xl p-8 sm:p-14 relative min-h-[1050px] transition-all duration-200 select-text"
                  style={{
                    width: fitWidth ? "100%" : `${720 * (zoom / 100)}px`,
                    fontFamily: "Georgia, serif",
                  }}
                >
                  {/* Elegant Academic Header Watermark */}
                  <div className="border-b border-slate-200 pb-3.5 mb-10 flex justify-between items-center text-[9px] text-slate-400 font-bold uppercase tracking-widest select-none">
                    <span className="text-[#E8400C] tracking-wide">Dhirubhai Ambani University</span>
                    <span>Course Policy Outline Specification</span>
                  </div>

                  {/* Syllabus Content with serif document typeface styles */}
                  <div className="prose prose-slate max-w-none text-slate-800 text-[13px] leading-relaxed">
                    <MarkdownRenderer content={courseContent} />
                  </div>

                  {/* Elegant Academic Footer Watermark */}
                  <div className="mt-14 pt-3.5 border-t border-slate-100 flex justify-between items-center text-[8px] text-slate-400 font-bold uppercase tracking-widest select-none">
                    <span>DAU Academic Registry &copy; {new Date().getFullYear()}</span>
                    <span>Official Copy (1 / 1 Pages)</span>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          /* Empty state */
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-950 text-slate-400 select-none">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-full mb-4">
              <svg className="w-10 h-10 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-base font-black text-white mb-1">Course Specification Archive</h3>
            <p className="text-xs text-slate-500 font-medium max-w-sm leading-relaxed">
              Select any course from the master catalogue list on the left to load its official PDF-simulated policy specification sheet.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
