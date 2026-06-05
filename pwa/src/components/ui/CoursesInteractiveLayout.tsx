"use client";

import React, { useState, useEffect } from "react";
import { CourseMetadata } from "@/lib/utils/courseParser";
import { fetchCourseContent } from "@/services/courses";
import CourseList from "./CourseList";
import CourseDetailViewer from "./CourseDetailViewer";
import CourseBookletViewer from "./CourseBookletViewer";

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
  const [viewingFullBooklet, setViewingFullBooklet] = useState(true);
  const [viewingOriginalPdf, setViewingOriginalPdf] = useState(true);

  // PDF Viewer Simulation states
  const [zoom, setZoom] = useState(100);
  const [fitWidth, setFitWidth] = useState(false);

  const handleZoomIn = () => setZoom((prev) => Math.min(prev + 10, 150));
  const handleZoomOut = () => setZoom((prev) => Math.max(prev - 10, 50));
  const handleZoomReset = () => setZoom(100);
  const handleToggleFitWidth = () => setFitWidth((prev) => !prev);
  const handleToggleViewMode = () => setViewingOriginalPdf((prev) => !prev);

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

  useEffect(() => {
    if (!viewingFullBooklet && filteredCourses.length > 0 && !selectedCourse && window.innerWidth >= 768) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      handleSelectCourse(filteredCourses[0]);
    }
  }, [filteredCourses, selectedCourse, viewingFullBooklet]);

  // Extract unique terms for filter pills
  const terms = ["All", ...Array.from(new Set(courses.map((c) => c.term)))];

  const handleSelectBooklet = () => {
    setViewingFullBooklet(true);
    setSelectedCourse(null);
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-[calc(100vh-210px)] min-h-[500px]">
      <CourseList
        courses={filteredCourses}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        terms={terms}
        selectedTerm={selectedTerm}
        onSelectTerm={setSelectedTerm}
        viewingFullBooklet={viewingFullBooklet}
        onSelectBooklet={handleSelectBooklet}
        selectedCourse={selectedCourse}
        onSelectCourse={handleSelectCourse}
      />

      <div className="md:col-span-8 flex flex-col h-full overflow-hidden bg-slate-900 rounded-[24px] border border-slate-800 shadow-xl">
        {viewingFullBooklet ? (
          <CourseBookletViewer />
        ) : selectedCourse ? (
          <CourseDetailViewer
            course={selectedCourse}
            content={courseContent}
            loading={loadingContent}
            viewingOriginalPdf={viewingOriginalPdf}
            onToggleViewMode={handleToggleViewMode}
            zoom={zoom}
            onZoomIn={handleZoomIn}
            onZoomOut={handleZoomOut}
            onZoomReset={handleZoomReset}
            fitWidth={fitWidth}
            onToggleFitWidth={handleToggleFitWidth}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-950 text-slate-400 select-none">
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-full mb-4">
              <svg className="w-10 h-10 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-base font-black text-white mb-1">Course Specification Archive</h3>
            <p className="text-xs text-slate-505 font-medium max-w-sm leading-relaxed">
              Select any course from the master catalogue list on the left to load its official PDF-simulated policy specification sheet.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
