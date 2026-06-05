import React from "react";
import { CourseMetadata } from "@/lib/utils/courseParser";

interface CourseListProps {
  courses: CourseMetadata[];
  searchQuery: string;
  onSearchChange: (query: string) => void;
  terms: string[];
  selectedTerm: string;
  onSelectTerm: (term: string) => void;
  viewingFullBooklet: boolean;
  onSelectBooklet: () => void;
  selectedCourse: CourseMetadata | null;
  onSelectCourse: (course: CourseMetadata) => void;
}

export default function CourseList({
  courses,
  searchQuery,
  onSearchChange,
  terms,
  selectedTerm,
  onSelectTerm,
  viewingFullBooklet,
  onSelectBooklet,
  selectedCourse,
  onSelectCourse,
}: CourseListProps) {
  return (
    <div className="md:col-span-4 flex flex-col bg-white border border-[#E2E8F0] rounded-[24px] overflow-hidden h-full shadow-sm">
      <div className="p-4 border-b border-[#E2E8F0] bg-slate-50/50 space-y-3">
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
            onChange={(e) => onSearchChange(e.target.value)}
            className="w-full bg-white border border-[#E2E8F0] rounded-[16px] pl-10 pr-4 py-2.5 text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:border-primary-dau focus:ring-1 focus:ring-primary-dau/20 transition-all duration-200"
          />
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-none">
          {terms.map((term) => (
            <button
              key={term}
              type="button"
              onClick={() => onSelectTerm(term)}
              className={`px-3 py-1.5 rounded-full text-[10px] font-black tracking-wider uppercase whitespace-nowrap transition-all duration-200 ${
                selectedTerm === term
                  ? "bg-primary-dau text-white shadow-md shadow-primary-dau/15"
                  : "bg-slate-100 text-slate-505 hover:text-slate-900 hover:bg-slate-200"
              }`}
            >
              {term}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <button
          type="button"
          onClick={onSelectBooklet}
          className={`w-full text-left p-4 rounded-[16px] transition-all duration-200 border flex items-center justify-between gap-3 ${
            viewingFullBooklet
              ? "bg-orange-50/80 border-orange-200 text-primary-dau shadow-sm font-bold border-l-4 border-l-primary-dau pl-3.5"
              : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700 hover:border-slate-300"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <div className="bg-primary-dau text-white text-[9px] font-black tracking-tighter px-1.5 py-0.5 rounded leading-none">
              PDF
            </div>
            <div className="flex flex-col">
              <span className={`text-xs font-black ${viewingFullBooklet ? "text-primary-dau" : "text-slate-900"}`}>
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

        {courses.length > 0 ? (
          courses.map((course) => {
            const isSelected = selectedCourse?.id === course.id;

            return (
              <button
                key={course.id}
                type="button"
                onClick={() => onSelectCourse(course)}
                className={`w-full text-left p-4 rounded-[16px] transition-all duration-200 border ${
                  isSelected
                    ? "bg-orange-50/80 border-orange-200 text-primary-dau shadow-sm font-bold border-l-4 border-l-primary-dau pl-3.5"
                    : "bg-white border-transparent hover:bg-slate-50 hover:border-slate-100 text-slate-700"
                }`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-black ${
                      isSelected
                        ? "bg-primary-dau text-white"
                        : "bg-orange-50 text-primary-dau border border-orange-100"
                    }`}
                  >
                    {course.code}
                  </span>
                  <span className="text-[9px] font-black tracking-wide uppercase text-slate-400">
                    {course.term}
                  </span>
                </div>
                <h3 className={`text-xs font-black line-clamp-1 ${
                  isSelected ? "text-primary-dau" : "text-slate-900"
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
            <p className="text-xs text-slate-505 font-bold">No courses found</p>
          </div>
        )}
      </div>
    </div>
  );
}
