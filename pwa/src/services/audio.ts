export interface TranscribeResult {
  success: boolean;
  text?: string;
  error?: string;
}

export async function transcribeAudio(payload: {
  audioBase64: string;
  filename: string;
}): Promise<TranscribeResult> {
  try {
    const res = await fetch("/api/audio", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) return { success: false, error: `HTTP ${res.status}` };
    return (await res.json()) as TranscribeResult;
  } catch (e) {
    return { success: false, error: e instanceof Error ? e.message : "network error" };
  }
}
