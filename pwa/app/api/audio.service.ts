export interface TranscribeResult {
  success: boolean;
  text?: string;
  error?: string;
}

interface SpeechResponse {
  text?: string;
  transcript?: string;
  error?: string;
}

export async function transcribeAudio(payload: {
  audio: Blob;
  filename: string;
}): Promise<TranscribeResult> {
  try {
    const mime =
      payload.audio.type ||
      (payload.filename.endsWith(".wav") ? "audio/wav" : "audio/webm");

    const form = new FormData();
    form.append(
      "file",
      new File([payload.audio], payload.filename, { type: mime }),
    );

    const res = await fetch("/api/speech", { method: "POST", body: form });
    const data = (await res.json().catch(() => null)) as SpeechResponse | null;

    if (!res.ok || !data) {
      return { success: false, error: data?.error ?? `HTTP ${res.status}` };
    }
    return { success: true, text: data.text ?? data.transcript ?? "" };
  } catch (e) {
    return {
      success: false,
      error: e instanceof Error ? e.message : "network error",
    };
  }
}
