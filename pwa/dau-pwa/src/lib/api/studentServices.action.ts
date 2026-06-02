"use server";

import fs from "fs";
import path from "path";
import { z } from "zod";

const fetchStudentServiceDocumentSchema = z.object({
  fileName: z.string().endsWith(".md", "Only markdown files are permitted")
});

export interface FetchStudentServiceDocumentResult {
  success: boolean;
  content: string;
}

/**
 * Fetch a student service markdown document safely from the data folder
 */
export async function fetchStudentServiceDocument(
  payload: { fileName: string }
): Promise<FetchStudentServiceDocumentResult> {
  const validated = fetchStudentServiceDocumentSchema.safeParse(payload);
  if (!validated.success) {
    throw new Error("Invalid input: " + validated.error.message);
  }

  const { fileName } = validated.data;

  // Define allowed root directories for searching
  const rootDirs = [
    path.join(process.cwd(), "data", "Team D", "madhav-data", "student_services"),
    path.join(process.cwd(), "data", "intranet", "academics"),
    path.join(process.cwd(), "data", "Team C"),
    path.join(process.cwd(), "data", "Team D", "madhav-data", "faculty")
  ];

  try {
    let filePath = "";

    // Resolve and verify that the file path stays inside the corresponding allowed root
    for (const rootDir of rootDirs) {
      const resolved = path.resolve(rootDir, fileName);
      if (resolved.startsWith(rootDir + path.sep)) {
        if (fs.existsSync(resolved)) {
          filePath = resolved;
          break;
        }
      }
    }

    if (!filePath) {
      // In case path is requested but not found, check path safety against default root to prevent path traversal
      const defaultDir = rootDirs[0];
      const resolvedFallback = path.resolve(defaultDir, fileName);
      if (!resolvedFallback.startsWith(defaultDir + path.sep)) {
        throw new Error("Invalid file path");
      }
      return {
        success: false,
        content: `Document ${fileName} not found on disk.`,
      };
    }

    let content = fs.readFileSync(filePath, "utf-8");

    // Strip YAML frontmatter
    if (content.startsWith("---")) {
      const endOfFrontmatter = content.indexOf("---", 3);
      if (endOfFrontmatter !== -1) {
        content = content.substring(endOfFrontmatter + 3).trim();
      }
    }

    return {
      success: true,
      content,
    };
  } catch (error) {
    console.error(`Failed to fetch document ${fileName}:`, error);
    return {
      success: false,
      content: "Error: Failed to retrieve document content.",
    };
  }
}

export interface FacultyMember {
  name: string;
  designation: string;
  email: string;
  office: string;
  specialization: string;
  fileName: string;
}

/**
 * Scans faculty directory and parses all records
 */
export async function getFacultyList(): Promise<FacultyMember[]> {
  try {
    const facultyDir = path.join(process.cwd(), "data", "Team D", "madhav-data", "faculty");
    if (!fs.existsSync(facultyDir)) {
      return [];
    }

    const files = fs.readdirSync(facultyDir);
    const facultyFiles = files.filter(
      (f) =>
        f.endsWith(".md") &&
        f !== "professor_of_practice_list.md" &&
        f !== "teaching_fellows_list.md" &&
        f !== "staff_list.md"
    );

    const facultyList: FacultyMember[] = [];

    for (const file of facultyFiles) {
      const filePath = path.join(facultyDir, file);
      const content = fs.readFileSync(filePath, "utf-8");

      // Extract title metadata
      let name = file
        .replace(/^faculty_/, "")
        .replace(/\.md$/, "")
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      
      const titleMatch = content.match(/title:\s*"(.*?)"/);
      if (titleMatch) {
        name = titleMatch[1];
      }

      const lines = content.split("\n").map((l) => l.trim());

      let email = "";
      let office = "";
      let specialization = "";
      let designation = "Assistant Professor";

      // Simple parsing loop
      let inMainContent = false;
      const mainContentLines: string[] = [];

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (line.startsWith("email:") || line.startsWith("- **Email:**")) {
          const m = line.match(
            /(?:email:\s*|Email:\*\*\s*)([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/i
          );
          if (m) email = m[1];
        }
        if (line.includes("@dau.ac.in") || line.includes("@daiict.ac.in")) {
          const m = line.match(/([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/);
          if (m && !email) email = m[1];
        }
        if (
          line.startsWith("# 3") ||
          line.startsWith("# 4") ||
          line.includes("FB-") ||
          line.includes("Lab")
        ) {
          office = line.replace(/^#\s*/, "");
        }
        if (line.toLowerCase() === "specialization") {
          // Look at next non-empty lines
          let j = i + 1;
          while (j < lines.length && lines[j] === "") j++;
          if (j < lines.length) specialization = lines[j];
        }
        if (line.toLowerCase() === "# main content") {
          inMainContent = true;
          continue;
        }
        if (inMainContent) {
          if (line.startsWith("#")) {
            inMainContent = false;
          } else if (line !== "") {
            mainContentLines.push(line);
          }
        }
      }

      // Infer designation from main content lines
      if (mainContentLines.length > 0) {
        const filtered = mainContentLines.filter(
          (l) => l.toLowerCase() !== name.toLowerCase() && !l.startsWith("###")
        );
        if (filtered.length > 0) {
          designation = filtered[0];
          if (designation.length > 100) {
            designation = designation.substring(0, 100) + "...";
          }
        }
      }

      facultyList.push({
        name,
        designation,
        email: email || "contact@dau.ac.in",
        office: office || "Faculty Block, DAU",
        specialization: specialization || "Computer Science / ICT",
        fileName: file,
      });
    }

    return facultyList.sort((a, b) => a.name.localeCompare(b.name));
  } catch (err) {
    console.error("Error parsing faculty directory:", err);
    return [];
  }
}

export interface EventItem {
  title: string;
  date: string;
  fileName: string;
  category: string;
}

/**
 * Scans events database under Team C and returns aggregated events list
 */
export async function getEventsList(): Promise<EventItem[]> {
  try {
    const eventsList: EventItem[] = [];

    // 1. Scan Team C files
    const teamCDir = path.join(process.cwd(), "data", "Team C");
    if (fs.existsSync(teamCDir)) {
      const files = fs.readdirSync(teamCDir).filter(
        (f) => f.endsWith(".md") && f !== "team-c.md" && f !== "validation_report.md"
      );
      
      for (const file of files) {
        const filePath = path.join(teamCDir, file);
        const content = fs.readFileSync(filePath, "utf-8");

        let title = file
          .replace(/\.md$/, "")
          .replace(/_/g, " ")
          .replace(/\b\w/g, (c) => c.toUpperCase());
        
        let date = "2026-05-30";

        const titleMatch = content.match(/title:\s*"(.*?)"/);
        if (titleMatch) title = titleMatch[1];

        const dateMatch = content.match(/scraped_date:\s*"(.*?)"/);
        if (dateMatch) date = dateMatch[1];

        let category = "Campus News";
        const lowerFile = file.toLowerCase();
        if (
          lowerFile.includes("sports") ||
          lowerFile.includes("concours") ||
          lowerFile.includes("plays")
        ) {
          category = "Sports Event";
        } else if (
          lowerFile.includes("workshop") ||
          lowerFile.includes("seminar") ||
          lowerFile.includes("bootcamp") ||
          lowerFile.includes("symposium")
        ) {
          category = "Workshop / Seminar";
        } else if (lowerFile.includes("alumni") || lowerFile.includes("reunion")) {
          category = "Alumni Connect";
        }

        eventsList.push({
          title,
          date,
          fileName: file,
          category,
        });
      }
    }

    // 2. Add key events from events.md
    eventsList.push(
      {
        title: "Artificial Intelligence in Internet of Things (AIoT): Concepts & Architectures",
        date: "2026-06-15",
        fileName: "events.md",
        category: "Workshop / Seminar",
      },
      {
        title: "Two-Day Workshop on AI Engineering Bootcamp 2026",
        date: "2026-05-16",
        fileName: "events.md",
        category: "Workshop / Seminar",
      },
      {
        title: "Coffee and Connect with Alumni Mr. Bhavesh Manglani, Co-Founder of Delhivery",
        date: "2026-04-23",
        fileName: "events.md",
        category: "Alumni Connect",
      },
      {
        title: "Workshop on RTL to GDS-II: VLSI Design and Hardware Security",
        date: "2026-07-06",
        fileName: "events.md",
        category: "Workshop / Seminar",
      }
    );

    return eventsList.sort((a, b) => b.date.localeCompare(a.date));
  } catch (err) {
    console.error("Error parsing events directory:", err);
    return [];
  }
}


