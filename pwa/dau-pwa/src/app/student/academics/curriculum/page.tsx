import React from "react";
import fs from "fs";
import path from "path";
import MarkdownRenderer from "@/components/features/student/MarkdownRenderer";

export const dynamic = "force-dynamic";

export default function CurriculumPage() {
  let content = "";
  try {
    const filePath = path.join(
      process.cwd(),
      "data",
      "Team D",
      "madhav-data",
      "student_services",
      "programs_of_study.md"
    );
    if (fs.existsSync(filePath)) {
      const fileContent = fs.readFileSync(filePath, "utf-8");
      // Strip frontmatter
      if (fileContent.startsWith("---")) {
        const endOfFrontmatter = fileContent.indexOf("---", 3);
        if (endOfFrontmatter !== -1) {
          content = fileContent.substring(endOfFrontmatter + 3).trim();
        } else {
          content = fileContent;
        }
      } else {
        content = fileContent;
      }
    } else {
      content = "Curriculum specifications not found on disk.";
    }
  } catch (error) {
    console.error("Error loading curriculum page:", error);
    content = "Error: Failed to load curriculum specifications.";
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="border-b border-border-dau pb-4">
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground">
          Program Curriculum
        </h1>
        <p className="text-sm text-text-muted mt-1">
          Review academic pathways, credits structures, and degree requirements for UG, PG, Dual Degrees, and Doctoral programs.
        </p>
      </div>

      {/* Main Content Card */}
      <div className="bg-white border border-border-dau rounded-3xl p-6 sm:p-10 shadow-sm max-w-4xl">
        <div className="prose prose-slate max-w-none">
          <MarkdownRenderer content={content} />
        </div>
      </div>
    </div>
  );
}
