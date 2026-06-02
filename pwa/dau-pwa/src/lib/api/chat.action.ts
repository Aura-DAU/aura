"use server";

import fs from "fs";
import path from "path";
import { z } from "zod";
import { callClaude } from "@/lib/ai/aiClient";
import { AURA_SYSTEM_PROMPT } from "@/lib/ai/prompts/chatPrompt";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface StudentProfile {
  name: string;
  branch: string;
  year: string;
  semester: string;
  interests: string;
}

interface SearchDocument {
  title: string;
  content: string;
  filePath: string;
  score: number;
}

export interface Citation {
  title: string;
  file: string;
}

export interface AskAuraResult {
  success: boolean;
  content: string;
  citations: Citation[];
}

const chatMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string()
});

const studentProfileSchema = z.object({
  name: z.string(),
  branch: z.string(),
  year: z.string(),
  semester: z.string(),
  interests: z.string()
});

const askAuraSchema = z.object({
  message: z.string().min(1, "Message is required"),
  history: z.array(chatMessageSchema),
  studentProfile: studentProfileSchema
});

/**
 * RAG Chat Server Action for AURA
 */
export async function askAura(payload: {
  message: string;
  history: ChatMessage[];
  studentProfile: StudentProfile;
}): Promise<AskAuraResult> {
  const validated = askAuraSchema.safeParse(payload);
  if (!validated.success) {
    return {
      success: false,
      content: "Invalid input: " + validated.error.message,
      citations: [],
    };
  }

  const { message, history, studentProfile } = validated.data;

  if (!message || typeof message !== "string") {
    throw new Error("Message is required.");
  }

  try {
    // 1. Gather all documents from directories
    const searchDocs: SearchDocument[] = [];
    const dirs = [
      { path: path.join(process.cwd(), "data", "Team D", "madhav-data", "student_services"), category: "Student Services" },
      { path: path.join(process.cwd(), "data", "Team D", "madhav-data", "faculty"), category: "Faculty Directory" },
      { path: path.join(process.cwd(), "data", "intranet", "academics"), category: "Academics" },
      { path: path.join(process.cwd(), "data", "Team C"), category: "Campus News" },
    ];

    const keywords = message
      .toLowerCase()
      .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()?]/g, "")
      .split(/\s+/)
      .filter((w) => w.length > 2);

    for (const dir of dirs) {
      if (fs.existsSync(dir.path)) {
        const files = fs.readdirSync(dir.path).filter((f) => f.endsWith(".md"));
        for (const file of files) {
          const filePath = path.join(dir.path, file);
          const rawContent = fs.readFileSync(filePath, "utf-8");
          
          let content = rawContent;
          if (content.startsWith("---")) {
            const end = content.indexOf("---", 3);
            if (end !== -1) content = content.substring(end + 3).trim();
          }

          // Simple keyword scoring
          let score = 0;
          const lowerContent = content.toLowerCase();
          for (const kw of keywords) {
            if (lowerContent.includes(kw)) {
              // Count occurrences
              const count = (lowerContent.match(new RegExp(kw, "g")) || []).length;
              score += count;
            }
          }

          if (score > 0) {
            // Extract document title from metadata or file name
            let title = file
              .replace(/\.md$/, "")
              .replace(/_/g, " ")
              .replace(/\b\w/g, (c) => c.toUpperCase());
            
            const titleMatch = rawContent.match(/title:\s*"(.*?)"/);
            if (titleMatch) title = titleMatch[1];

            searchDocs.push({
              title: `${title} (${dir.category})`,
              content: content.substring(0, 1500), // Limit snippet size
              filePath: file,
              score,
            });
          }
        }
      }
    }

    // Sort documents by relevance score
    searchDocs.sort((a, b) => b.score - a.score);
    const topMatches = searchDocs.slice(0, 3);

    // Build context string
    let groundingContext = "";
    if (topMatches.length > 0) {
      groundingContext = topMatches
        .map((doc, idx) => `[Source ${idx + 1}: ${doc.title} (${doc.filePath})]\n${doc.content}`)
        .join("\n\n---\n\n");
    } else {
      groundingContext = "No specific official policy document matches this query.";
    }

    // 2. Prepare personalized system prompt
    const studentProfileStr = `Name: ${studentProfile.name}\nBranch: ${studentProfile.branch}\nYear: ${studentProfile.year}\nSemester: ${studentProfile.semester}\nInterests: ${studentProfile.interests}`;
    const systemPrompt = AURA_SYSTEM_PROMPT
      .replace("{{STUDENT_PROFILE}}", studentProfileStr)
      .replace("{{GROUNDING_CONTEXT}}", groundingContext);

    // 3. Check for Claude API Key
    if (process.env.ANTHROPIC_API_KEY) {
      const response = await callClaude({
        systemPrompt,
        userMessage: message,
        history,
      });

      return {
        success: response.success,
        content: response.content,
        citations: topMatches.map((doc) => ({ title: doc.title, file: doc.filePath })),
      };
    }

    // 4. Offline Fallback (RAG keyword matching search)
    let reply = "";
    if (topMatches.length > 0) {
      const bestDoc = topMatches[0];
      const cleanTitle = bestDoc.title.replace(/\(.*?\)/g, "").trim();
      
      reply = `**AURA Offline Assistant:** I found some official guidelines in **${cleanTitle}** that might help you.\n\n`;
      
      // Try to find a paragraph matching keywords in the best document
      const paragraphs = bestDoc.content.split("\n\n").filter((p) => p.trim().length > 20);
      let matchedParagraphs = paragraphs.filter((p) => {
        const lowerP = p.toLowerCase();
        return keywords.some((kw) => lowerP.includes(kw));
      });

      if (matchedParagraphs.length === 0) {
        matchedParagraphs = paragraphs.slice(0, 2);
      }

      reply += matchedParagraphs.slice(0, 3).join("\n\n");
      reply += `\n\n*Reference: You can read the full document on the **${cleanTitle}** pages or ask me in online mode.*`;
    } else {
      reply = `**AURA Offline Assistant:** I couldn't find any direct matches in the university databases for your query: "${message}".\n\nTry asking about:\n- Hostel regulations or curfews\n- Lost ID Card replacement workflows\n- Academic Calendars or timetables\n- Course details and syllabus`;
    }

    return {
      success: true,
      content: reply,
      citations: topMatches.map((doc) => ({ title: doc.title, file: doc.filePath })),
    };
  } catch (error) {
    console.error("Error in askAura server action:", error);
    return {
      success: false,
      content: "Error: AURA encountered an unexpected error while orchestrating your request.",
      citations: [],
    };
  }
}
