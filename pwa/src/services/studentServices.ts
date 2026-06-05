export interface EventItem {
  fileName: string;
  title: string;
  category: string;
  date: string;
}

export interface FacultyMember {
  fileName: string;
  name: string;
  designation: string;
  specialization: string;
  office: string;
  email: string;
}

export interface DocumentResult {
  success: boolean;
  content: string;
  error?: string;
}

export async function fetchStudentServiceDocument(payload: {
  fileName: string;
}): Promise<DocumentResult> {
  try {
    const res = await fetch(`/api/student-services?file=${encodeURIComponent(payload.fileName)}`);
    if (!res.ok) return { success: false, content: "", error: `HTTP ${res.status}` };
    return (await res.json()) as DocumentResult;
  } catch (e) {
    return { success: false, content: "", error: e instanceof Error ? e.message : "network error" };
  }
}

export async function getEventsList(): Promise<EventItem[]> {
  try {
    const res = await fetch("/api/student-services/events");
    if (!res.ok) return [];
    return (await res.json()) as EventItem[];
  } catch {
    return [];
  }
}

export async function getFacultyList(): Promise<FacultyMember[]> {
  try {
    const res = await fetch("/api/student-services/faculty");
    if (!res.ok) return [];
    return (await res.json()) as FacultyMember[];
  } catch {
    return [];
  }
}
