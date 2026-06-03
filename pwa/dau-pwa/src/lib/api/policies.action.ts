"use server";

import { z } from "zod";
import { getDocumentContent } from "@/lib/utils/courseParser";

const fetchPolicyContentSchema = z.object({
  fileName: z.string().regex(/^academic_policy_.*\.md$/, "Invalid file name pattern"),
});

export interface FetchPolicyContentResult {
  success: boolean;
  content: string;
}

/**
 * Fetch academic policy markdown content safely from data folder
 */
export async function fetchPolicyContent(
  payload: { fileName: string }
): Promise<FetchPolicyContentResult> {
  // Validate input with Zod
  const validated = fetchPolicyContentSchema.safeParse(payload);
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
    console.error(`Failed to fetch policy content for ${fileName}:`, error);
    return {
      success: false,
      content: "Error: Failed to retrieve academic policy content.",
    };
  }
}
