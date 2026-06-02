import fs from "fs";
import path from "path";

export interface CourseMetadata {
  id: string;
  code: string;
  title: string;
  term: string;
  fileName: string;
  filePath: string;
  pdfPath?: string;
}

export interface PolicyMetadata {
  id: string;
  title: string;
  category: string;
  fileName: string;
  filePath: string;
}

const DATA_DIR = path.join(process.cwd(), "data", "intranet", "academics");

/**
 * Format string to Title Case
 */
function toTitleCase(str: string): string {
  return str
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

/**
 * Scan academics directory and parse metadata of course policy files
 */
export function getCoursesList(): CourseMetadata[] {
  try {
    if (!fs.existsSync(DATA_DIR)) {
      return [];
    }

    const files = fs.readdirSync(DATA_DIR);
    const courseFiles = files.filter(
      (file) => file.startsWith("course_policy_") && file.endsWith(".md")
    );

    // Scan public/documents folder for individual course policy PDFs
    const documentsDir = path.join(process.cwd(), "public", "documents");
    let pdfFiles: string[] = [];
    if (fs.existsSync(documentsDir)) {
      pdfFiles = fs.readdirSync(documentsDir).filter(
        (f) => f.endsWith(".pdf") && f.toLowerCase() !== "course_booklet_for_autumn_2025-26.pdf"
      );
    }

    const coursesMap = new Map<string, CourseMetadata>();

    courseFiles.forEach((file) => {
      // Example file: course_policy_sc107_sc_107_calculus_autumn_2025_page_17.md
      // Example file: course_policy_it549_it549_deep_learning_winter.md
      
      const cleanName = file
        .replace(/^course_policy_/, "")
        .replace(/\.md$/, "");

      // Split into parts to extract course code, term, etc.
      const parts = cleanName.split("_");
      
      // Try to find the course code (e.g. sc107, it549, mc116, hm404)
      let code = "";
      for (const part of parts) {
        if (/^[a-zA-Z]{2,3}\d{3}$/.test(part)) {
          code = part.toUpperCase();
          break;
        }
      }
      
      // Fallback code if not found in standard regex
      if (!code && parts.length > 0) {
        code = parts[0].toUpperCase();
      }

      // Determine term/semester
      let term = "Winter";
      if (cleanName.includes("autumn_2025")) {
        term = "Autumn 2025";
      } else if (cleanName.includes("autumn")) {
        term = "Autumn";
      } else if (cleanName.includes("winter_2026")) {
        term = "Winter 2026";
      } else if (cleanName.includes("winter")) {
        term = "Winter";
      }

      // Title extraction: remove course policy, code prefixes, term suffixes, and page numbers
      let titleWords = cleanName
        .replace(/^[a-zA-Z]{2,4}\d{1,4}/, "") // Remove code at start if any
        .replace(/page_\d+$/, "") // Remove page numbers at end
        .replace(/_page_\d+$/, "")
        .replace(/_autumn_\d+$/, "") // Remove term suffix
        .replace(/_autumn$/, "")
        .replace(/_winter_\d+$/, "")
        .replace(/_winter$/, "")
        .replace(/^[a-zA-Z_]{2,4}_\d{1,4}/, "") // Remove repeating code parts like sc_107
        .split("_")
        .filter((w) => w.length > 0 && !w.match(/^\d+$/) && w !== "course" && w !== "policy");

      // Filter out duplicate or repeating words (like code)
      titleWords = titleWords.filter(
        (w) => w.toUpperCase() !== code && w.toLowerCase() !== "page"
      );

      let title = toTitleCase(titleWords.join(" "));
      
      // Fallbacks for empty titles
      if (!title || title.trim().length === 0) {
        title = toTitleCase(cleanName.replace(/_/g, " "));
      }

      // Deduplicate courses by choosing the most complete record or autumn_2025 over others
      const courseId = `${code}-${term.replace(/\s+/g, "")}`.toUpperCase();

      // Find matching course PDF by checking if file prefix matches the course code
      const matchedPdf = pdfFiles.find((f) => {
        const lowerCode = code.toLowerCase();
        const cleanFile = f.toLowerCase().replace(/[\s-_]+/g, "");
        return cleanFile.startsWith(lowerCode);
      });

      const newCourse: CourseMetadata = {
        id: courseId,
        code,
        title,
        term,
        fileName: file,
        filePath: path.join(DATA_DIR, file),
        pdfPath: matchedPdf ? `/documents/${matchedPdf}` : undefined,
      };

      if (!coursesMap.has(courseId)) {
        coursesMap.set(courseId, newCourse);
      } else {
        // Keep the one with the longer/more informative title
        const existing = coursesMap.get(courseId)!;
        if (title.length > existing.title.length) {
          coursesMap.set(courseId, newCourse);
        }
      }
    });

    return Array.from(coursesMap.values()).sort((a, b) => {
      // Sort by code first, then title
      if (a.code !== b.code) return a.code.localeCompare(b.code);
      return a.title.localeCompare(b.title);
    });
  } catch (error) {
    console.error("Error reading courses:", error);
    return [];
  }
}

/**
 * Scan academics directory and parse metadata of academic policy files
 */
export function getPoliciesList(): PolicyMetadata[] {
  try {
    if (!fs.existsSync(DATA_DIR)) {
      return [];
    }

    const files = fs.readdirSync(DATA_DIR);
    const policyFiles = files.filter(
      (file) => file.startsWith("academic_policy_") && file.endsWith(".md")
    );

    const policies: PolicyMetadata[] = [];

    policyFiles.forEach((file) => {
      const cleanName = file
        .replace(/^academic_policy_/, "")
        .replace(/\.md$/, "");

      if (!cleanName || cleanName.trim().length === 0) return;

      const title = toTitleCase(cleanName);
      
      // Grouping category based on file content/title
      let category = "General Rules";
      if (cleanName.includes("exam") || cleanName.includes("malpractices")) {
        category = "Examinations";
      } else if (cleanName.includes("registration") || cleanName.includes("fees")) {
        category = "Admissions & Fees";
      } else if (cleanName.includes("requirements") || cleanName.includes("curriculum")) {
        category = "Program Requirements";
      } else if (cleanName.includes("conduct") || cleanName.includes("disciplinary") || cleanName.includes("vehicle") || cleanName.includes("leave")) {
        category = "Student Life & Conduct";
      }

      policies.push({
        id: cleanName,
        title,
        category,
        fileName: file,
        filePath: path.join(DATA_DIR, file),
      });
    });

    return policies.sort((a, b) => a.title.localeCompare(b.title));
  } catch (error) {
    console.error("Error reading policies:", error);
    return [];
  }
}

/**
 * Load file content of a specific document
 */
export function getDocumentContent(fileName: string): string {
  try {
    const filePath = path.join(DATA_DIR, fileName);
    if (!fs.existsSync(filePath)) {
      return "Document not found.";
    }
    
    // Read the file and strip YAML frontmatter if present
    let content = fs.readFileSync(filePath, "utf-8");
    if (content.startsWith("---")) {
      const endOfFrontmatter = content.indexOf("---", 3);
      if (endOfFrontmatter !== -1) {
        content = content.substring(endOfFrontmatter + 3).trim();
      }
    }
    return content;
  } catch (error) {
    console.error(`Error reading document content for ${fileName}:`, error);
    return "Error reading document content.";
  }
}
