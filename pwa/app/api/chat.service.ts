export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  timestamp?: number;
}

export interface StudentProfile {
  name: string;
  branch: string;
  year: string;
  semester: string;
  interests: string;
}

export interface Citation {
  title: string;
  file: string;
}

export interface AskAuraResult {
  success: boolean;
  content?: string;
  citations?: Citation[];
  error?: string;
}

interface BackendSource {
  title?: string;
  url?: string;
  file?: string;
  source?: string;
  [key: string]: unknown;
}

interface BackendResponse {
  answer?: string;
  sources?: BackendSource[];
  error?: string;
  detail?: string;
}

// Must match the Zod limits in app/api/chat/route.ts.
export const MAX_QUESTION_CHARS = 2000;
export const MAX_HISTORY_TURN_CHARS = 8000;

function normaliseCitations(sources: BackendSource[] | undefined): Citation[] {
  if (!sources) return [];
  return sources.map((s, i) => ({
    title: s.title ?? `Source ${i + 1}`,
    file: s.file ?? s.source ?? s.url ?? "",
  }));
}

export async function askAura(payload: {
  message: string;
  history: ChatMessage[];
  studentProfile: StudentProfile;
}): Promise<AskAuraResult> {
  try {
    // Keep payloads inside the proxy's Zod limits: long assistant answers
    // would otherwise poison the stored history and 400 every later request.
    const slicedHistory = payload.history.slice(-20).map((turn) =>
      turn.content.length > MAX_HISTORY_TURN_CHARS
        ? { ...turn, content: turn.content.slice(0, MAX_HISTORY_TURN_CHARS) }
        : turn,
    );

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: payload.message.slice(0, MAX_QUESTION_CHARS),
        history: slicedHistory,
        studentProfile: payload.studentProfile,
      }),
    });

    const data = (await res.json().catch(() => null)) as BackendResponse | null;

    if (!res.ok || !data) {
      return {
        success: false,
        error: data?.error ?? `HTTP ${res.status}`,
      };
    }

    return {
      success: true,
      content: data.answer ?? "",
      citations: normaliseCitations(data.sources),
    };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "network error",
    };
  }
}
