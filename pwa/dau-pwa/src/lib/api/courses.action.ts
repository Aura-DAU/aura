"use server";

import { z } from "zod";
import { getDocumentContent } from "@/lib/utils/courseParser";

const fetchCourseContentSchema = z.object({
  fileName: z.string().regex(/^course_policy_.*\.md$/, "Invalid file name pattern"),
});

export interface FetchCourseContentResult {
  success: boolean;
  content: string;
}

/**
 * Fetch course markdown content safely from data folder
 */
export async function fetchCourseContent(
  payload: { fileName: string }
): Promise<FetchCourseContentResult> {
  // Validate input with Zod
  const validated = fetchCourseContentSchema.safeParse(payload);
  if (!validated.success) {
    throw new Error("Invalid input: " + validated.error.message);
  }

  const { fileName } = validated.data;
  
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
