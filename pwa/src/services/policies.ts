import type { DocumentResult } from "./courses";

export async function fetchPolicyContent(payload: { fileName: string }): Promise<DocumentResult> {
  try {
    const res = await fetch(`/api/policies?file=${encodeURIComponent(payload.fileName)}`);
    if (!res.ok) return { success: false, content: "", error: `HTTP ${res.status}` };
    return (await res.json()) as DocumentResult;
  } catch (e) {
    return { success: false, content: "", error: e instanceof Error ? e.message : "network error" };
  }
}
