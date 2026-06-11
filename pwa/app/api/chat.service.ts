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
    // Limit history payload size to prevent validation and token limit issues
    const slicedHistory = payload.history.slice(-20);

    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: payload.message,
        history: slicedHistory,
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
