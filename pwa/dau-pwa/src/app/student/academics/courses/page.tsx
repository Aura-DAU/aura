import React from "react";
import { getCoursesList } from "@/lib/utils/courseParser";
import CoursesInteractiveLayout from "@/components/features/student/CoursesInteractiveLayout";

// Force dynamic rendering since we are reading from filesystem at request time
export const dynamic = "force-dynamic";

export default function CoursesPage() {
  const courses = getCoursesList();

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Courses & Syllabus
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Search the university catalog for detailed courses syllabus specifications, evaluations, and textbooks.
        </p>
      </div>

      {/* Main Interactive Master-Detail Portal Panel */}
      <CoursesInteractiveLayout initialCourses={courses} />
    </div>
  );
}
