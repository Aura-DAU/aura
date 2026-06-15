import { z } from "zod";
import { cookies } from "next/headers";

export const runtime = "nodejs";

// ─── Request schemas ──────────────────────────────────────────────────────────
const HistoryTurnSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().min(1).max(8000),
  timestamp: z.number().optional(),
});

const StudentProfileSchema = z.object({
  name: z.string().max(100),
  branch: z.string().max(100),
  year: z.string().max(50),
  semester: z.string().max(50),
  interests: z.string().max(300),
});

const BodySchema = z.object({
  question: z.string().min(1).max(2000),
  history: z.array(HistoryTurnSchema).max(100).optional(),
  studentProfile: StudentProfileSchema.optional(),
});

// ─── BACKEND_URL validation — prevents SSRF via env misconfiguration ──────────
// FIX: AWS S3 key leakage / SSRF — whitelist the backend origin so a
// misconfigured BACKEND_URL can never point to an internal metadata endpoint
// (169.254.169.254, IMDSv2, etc.) or an attacker-controlled server.
const RAW_BACKEND = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";
function validateBackendUrl(raw: string): URL {
  let parsed: URL;
  try {
    parsed = new URL(raw);
  } catch {
    throw new Error(`BACKEND_URL is not a valid URL: "${raw}"`);
  }

  const BLOCKED_HOSTS = [
    "169.254.169.254",   // AWS/GCP/Azure IMDS
    "metadata.google.internal",
    "169.254.170.2",     // ECS task metadata
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
  console.error("[chat/route] Invalid BACKEND_URL:", err);
  BACKEND_URL = "http://127.0.0.1:8000"; // safe fallback
}

// ─── In-process rate limiter — prevents chat API abuse ───────────────────────
// FIX: Login Replay / chat-spam — 30 requests per user per minute
interface ChatBucket { count: number; windowStart: number; }
const chatLimiter = new Map<string, ChatBucket>();
const CHAT_MAX = 30;
const CHAT_WINDOW_MS = 60_000;

function chatRateLimit(key: string): boolean {
  const now = Date.now();
  const b = chatLimiter.get(key);
  if (!b || now - b.windowStart > CHAT_WINDOW_MS) {
    chatLimiter.set(key, { count: 1, windowStart: now });
    return true; // allowed
  }
  if (b.count >= CHAT_MAX) return false; // blocked
  b.count++;
  return true;
}

// ─── Route handler ────────────────────────────────────────────────────────────
export async function POST(request: Request) {
  // FIX: Auth gate — only authenticated sessions may call /api/chat
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get("aura_session");
  if (!sessionCookie) {
    return Response.json({ error: "Unauthorized" }, { status: 401 });
  }

  let sessionEmail = "anonymous";
  try {
    const sess = JSON.parse(sessionCookie.value);
    sessionEmail = sess?.email ?? "anonymous";
  } catch { /* malformed cookie — still allow but treat as anon */ }

  // Rate limit by session email
  if (!chatRateLimit(sessionEmail)) {
    return Response.json(
      { error: "Too many requests. Please slow down." },
      { status: 429, headers: { "Retry-After": "60" } }
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const parsed = BodySchema.safeParse(body);
  if (!parsed.success) {
    return Response.json(
      { error: "Invalid request", details: parsed.error.flatten() },
      { status: 400 }
    );
  }

  try {
    const upstream = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsed.data),
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