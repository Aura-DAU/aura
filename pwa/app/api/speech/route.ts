import { cookies } from "next/headers";

export const runtime = "nodejs";

const RAW_BACKEND = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

function validateBackendUrl(raw: string): URL {
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error(`BACKEND_URL is not a valid URL: "${raw}"`);
  }

  const BLOCKED_HOSTS = [
    "169.254.169.254",
    "metadata.google.internal",
    "169.254.170.2",
  ];
  if (BLOCKED_HOSTS.includes(parsed.hostname)) {
    throw new Error(`BACKEND_URL targets a blocked internal host: ${parsed.hostname}`);
  }
  if (!["http:", "https:"].includes(parsed.protocol)) {
    throw new Error(`BACKEND_URL must use http or https, got: ${parsed.protocol}`);
  }
  return parsed;
}

let BACKEND_URL: string;
try {
  BACKEND_URL = validateBackendUrl(RAW_BACKEND).origin;
} catch (err) {
  console.error("[speech/route] Invalid BACKEND_URL:", err);
  BACKEND_URL = "http://127.0.0.1:8000";
}

// TODO: Move in-process rate limiting to a shared store (Redis/Upstash) before deploying.
interface SpeechBucket { count: number; windowStart: number; }
const speechLimiter = new Map<string, SpeechBucket>();
const SPEECH_MAX = 30;
const SPEECH_WINDOW_MS = 60_000;

function speechRateLimit(key: string): boolean {
  const now = Date.now();
  const b = speechLimiter.get(key);
  if (!b || now - b.windowStart > SPEECH_WINDOW_MS) {
    speechLimiter.set(key, { count: 1, windowStart: now });
    return true;
  }
  if (b.count >= SPEECH_MAX) return false;
  b.count++;
  return true;
}

export async function POST(request: Request) {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get("aura_session");
  if (!sessionCookie) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  let sessionEmail = "anonymous";
  try {
    const sess = JSON.parse(sessionCookie.value);
    sessionEmail = sess?.email ?? "anonymous";
  } catch {
    // Treat as anonymous but still proceed
  }

  if (!speechRateLimit(sessionEmail)) {
    return Response.json(
      { error: "Too many requests. Please slow down." },
      { status: 429, headers: { "Retry-After": "60" } }
    );
  }

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return Response.json({ error: "Invalid form data" }, { status: 400 });
  }

  const file = formData.get("file");
  if (!file || !(file instanceof File)) {
    return Response.json({ error: "Missing file parameter" }, { status: 400 });
  }

  try {
    const upstream = await fetch(`${BACKEND_URL}/speech`, {
      method: "POST",
      body: formData,
    });

    if (!upstream.ok) {
      const detail = await upstream.text().catch(() => "");
      return Response.json(
        { error: "Upstream error", status: upstream.status, detail },
        { status: 502 }
      );
    }

    const data = await upstream.json();
    return Response.json(data);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return Response.json({ error: "Backend unreachable", detail: msg }, { status: 502 });
  }
}