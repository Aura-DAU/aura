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

export async function askAura(payload: {
  message: string;
  history: ChatMessage[];
  studentProfile: StudentProfile;
}): Promise<AskAuraResult> {
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return { success: false, error: `HTTP ${res.status}` };
    return (await res.json()) as AskAuraResult;
  } catch (e) {
    return { success: false, error: e instanceof Error ? e.message : "network error" };
  }
}
