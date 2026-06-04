/**
 * HTTP adapter for the FastAPI RAG backend.
 *
 * This module is the single integration point between the Next.js server
 * actions and the external FastAPI service. All fetch configuration (base URL,
 * timeout, request shape) lives here so chat.action.ts stays clean.
 */

import { ChatMessage, StudentProfile, Citation } from "@/lib/api/chat.action";

// ---------------------------------------------------------------------------
// Request / Response types (mirror backend/app/models/schemas.py)
// ---------------------------------------------------------------------------

export interface RagChatRequest {
  message: string;
  history: ChatMessage[];
  student_profile: StudentProfile;
}

export interface RagChatResponse {
  success: boolean;
  content: string;
  citations: Citation[];
}

// ---------------------------------------------------------------------------
// Client
// ---------------------------------------------------------------------------

const TIMEOUT_MS = 10_000;

/**
 * POST <FASTAPI_RAG_URL>/api/chat with a 10-second timeout.
 *
 * Throws if:
 *  - FASTAPI_RAG_URL is not configured
 *  - The network request fails or times out
 *  - The server returns a non-2xx status
 *  - The response body is not valid JSON matching RagChatResponse
 */
export async function callRagPipeline(
  req: RagChatRequest
): Promise<RagChatResponse> {
  const baseUrl = process.env.FASTAPI_RAG_URL;
  if (!baseUrl) {
    throw new Error("FASTAPI_RAG_URL is not configured.");
  }

  const url = `${baseUrl.replace(/\/$/, "")}/api/chat`;

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

  const startMs = Date.now();

  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal: controller.signal,
    });

    if (process.env.NODE_ENV === "development") {
      console.debug(`[ragClient] POST ${url} → ${res.status} (${Date.now() - startMs}ms)`);
    }

    if (!res.ok) {
      throw new Error(`FastAPI returned HTTP ${res.status}: ${res.statusText}`);
    }

    const data: RagChatResponse = await res.json();
    return data;
  } finally {
    clearTimeout(timer);
  }
}
