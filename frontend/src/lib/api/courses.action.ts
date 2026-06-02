"use server";

import { getDocumentContent } from "@/lib/utils/courseParser";

/**
 * Fetch course markdown content safely from data folder
 */
export async function fetchCourseContent(payload: { fileName: string }) {
  // Validate input
  if (
    !payload ||
    typeof payload.fileName !== "string" ||
    !/^course_policy_.*\.md$/.test(payload.fileName)
  ) {
    throw new Error("Invalid file name pattern");
  }

  const { fileName } = payload;
  
  try {
    const content = getDocumentContent(fileName);
    return {
      success: true,
      content,
    };
  } catch (error) {
    console.error(`Failed to fetch course content for ${fileName}:`, error);
    return {
      success: false,
      content: "Error: Failed to retrieve course content.",
    };
  }
}
