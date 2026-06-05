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

function base64ToBlob(base64: string, mime: string): Blob {
  const binary = atob(base64);
  const len = binary.length;
  const bytes = new Uint8Array(len);
  for (let i = 0; i < len; i++) bytes[i] = binary.charCodeAt(i);
  return new Blob([bytes], { type: mime });
}

export async function transcribeAudio(payload: {
  audioBase64: string;
  filename: string;
}): Promise<TranscribeResult> {
  try {
    const mime = payload.filename.endsWith(".wav")
      ? "audio/wav"
      : "audio/webm";
    const blob = base64ToBlob(payload.audioBase64, mime);

    const form = new FormData();
    form.append("file", new File([blob], payload.filename, { type: mime }));

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
