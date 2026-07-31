import { getServerSession } from "next-auth"
import { cookies } from "next/headers"
import { randomUUID } from "crypto"
import { z } from "zod"

import { backendUrl, type BackendChatRequest } from "@/lib/api/backend"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export const maxDuration = 60

// Cookie identifying an anonymous guest browser (no Google sign-in). It
// carries no PII — just a random id — and lets the backend's 10/day quota
// (see server/rag/pipeline/rate_limiter.py) key on a stable per-browser
// identity instead of resetting on every request.
const GUEST_COOKIE = "aura-guest-id"
const GUEST_COOKIE_MAX_AGE = 60 * 60 * 24 * 365 // 1 year

const historyTurnSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().max(20_000),
})

const studentProfileSchema = z.object({
  name: z.string().max(200).optional(),
  branch: z.string().max(200).optional(),
  year: z.string().max(50).optional(),
  semester: z.string().max(50).optional(),
  interests: z.string().max(1000).optional(),
})

const requestSchema = z.object({
  question: z.string().min(1, "question is required").max(2000),
  history: z.array(historyTurnSchema).max(20).optional(),
  summary: z.string().max(20_000).optional(),
  threadId: z.string().max(64).optional(),
  studentProfile: studentProfileSchema.optional(),
})

function sseLine(data: unknown): string {
  return `data: ${JSON.stringify(data)}\n\n`
}

function toLineNumber(v: unknown): number | undefined {
  if (typeof v === "number" && Number.isFinite(v)) return v
  if (typeof v === "string" && v.trim() !== "" && !Number.isNaN(Number(v))) {
    return Number(v)
  }
  return undefined
}

function normaliseSource(
  s:
    | string
    | {
        file?: string
        url?: string
        title?: string
        path?: string
        start_line?: number | string | null
        end_line?: number | string | null
        visibility?: string
        authorization?: string[]
      },
): {
  file: string
  title?: string
  path?: string
  startLine?: number
  endLine?: number
  visibility?: string
  authorization?: string[]
} | null {
  if (typeof s === "string") return { file: s }
  if (s && typeof s === "object") {
    const file = s.file || s.url || s.path || ""
    if (file) {
      return {
        file,
        title: s.title,
        path: s.path || undefined,
        startLine: toLineNumber(s.start_line),
        endLine: toLineNumber(s.end_line),
        visibility: s.visibility,
        authorization: s.authorization,
      }
    }
  }
  return null
}

export async function POST(req: Request) {
  try {
    return await handleChatPost(req)
  } catch (err) {
    // Avoid Next's bare "Internal Server Error" text/plain body — clients that
    // expect JSON/SSE otherwise surface SyntaxError: Unexpected token 'I'...
    console.error("[chat] unhandled error:", err)
    return Response.json(
      { error: "Something went wrong while processing your request.", code: "INTERNAL" },
      { status: 500 },
    )
  }
}

async function handleChatPost(req: Request): Promise<Response> {
  const session = await getServerSession(authOptions)

  // Signed-in @dau.ac.in accounts use their real erpId/role (unlimited
  // quota, enforced server-side). Everyone else is treated as an
  // anonymous guest identified by a long-lived cookie, capped at 10
  // questions/day.
  let identity: {
    role: "student" | "faculty" | "admin" | "guest"
    erpId: string
    department?: string
    email?: string
  }

  if (session?.user?.erpId && session.user.role) {
    identity = {
      role: session.user.role,
      erpId: session.user.erpId,
      department: session.user.department,
      email: session.user.email ?? undefined,
    }
  } else {
    const cookieStore = await cookies()
    let guestId = cookieStore.get(GUEST_COOKIE)?.value
    if (!guestId || guestId.length > 64) {
      guestId = `GUEST-${randomUUID()}`
      cookieStore.set(GUEST_COOKIE, guestId, {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/",
        maxAge: GUEST_COOKIE_MAX_AGE,
      })
    }
    identity = { role: "guest", erpId: guestId }
  }

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return new Response("Invalid JSON", { status: 400 })
  }

  const parsed = requestSchema.safeParse(body)
  if (!parsed.success) {
    return new Response("Invalid request", { status: 400 })
  }

  let internalToken: string
  try {
    internalToken = signInternalJwt({
      role: identity.role,
      erpId: identity.erpId,
      department: identity.department,
      email: identity.email,
    })
  } catch (err) {
    console.error("[chat] failed to mint internal JWT:", err)
    return Response.json(
      { error: "Authentication is temporarily unavailable", code: "INTERNAL" },
      { status: 500 },
    )
  }

  // Map studentProfile → userProfile for FastAPI. History is the client's
  // unsummarised tail — the backend's ConversationMemory folds the rest into
  // `summary` — so forward it as-is rather than re-truncating here.
  const payload: BackendChatRequest = {
    question: parsed.data.question,
    history: parsed.data.history,
    summary: parsed.data.summary,
    threadId: parsed.data.threadId,
    studentProfile: parsed.data.studentProfile,
  }

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/chat/stream"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${internalToken}`,
      },
      body: JSON.stringify({
        question: payload.question,
        history: payload.history,
        summary: payload.summary,
        threadId: payload.threadId,
        userProfile: payload.studentProfile,
      }),
      signal: req.signal,
    })
  } catch (err) {
    console.error("[chat] backend unreachable:", err)
    return new Response("Backend unavailable", { status: 502 })
  }

  if (backendRes.status === 429) {
    return new Response("Question limit reached", { status: 429 })
  }

  if (!backendRes.ok) {
    const text = await backendRes.text().catch(() => "")
    console.error("[chat] backend error:", backendRes.status, text)
    return new Response(text || backendRes.statusText || "Backend error", {
      status: backendRes.status,
      headers: { "Content-Type": backendRes.headers.get("Content-Type") || "text/plain" },
    })
  }

  if (!backendRes.body) {
    console.error("[chat] backend returned no body for stream")
    return new Response("Invalid backend response", { status: 502 })
  }

  // Relay the backend SSE stream token-by-token instead of buffering the whole
  // answer (the old /chat proxy faked streaming by emitting one big delta).
  // text-delta / personal-data-flag / summary-update / thread-continuation and
  // [DONE] pass through untouched; citation events are re-normalised so the
  // client keeps its camelCased, side-drawer-ready Citation shape.
  const encoder = new TextEncoder()
  const decoder = new TextDecoder()

  const stream = new ReadableStream<Uint8Array>({
    async start(controller) {
      const reader = backendRes.body!.getReader()
      let buffer = ""

      const emit = (rawEvent: string): void => {
        const out = relaySseEvent(rawEvent)
        if (out) controller.enqueue(encoder.encode(out))
      }

      try {
        for (;;) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          // SSE events are delimited by a blank line.
          let sep: number
          while ((sep = buffer.indexOf("\n\n")) !== -1) {
            emit(buffer.slice(0, sep))
            buffer = buffer.slice(sep + 2)
          }
        }
        if (buffer.trim()) emit(buffer)
      } catch (err) {
        console.error("[chat] stream relay error:", err)
      } finally {
        controller.close()
      }
    },
    cancel() {
      // Client disconnected — tear down the upstream connection.
      void backendRes.body?.cancel().catch(() => {})
    },
  })

  const quotaHeader = backendRes.headers.get("X-Quota-Remaining")
  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      "X-Accel-Buffering": "no",
      ...(quotaHeader ? { "X-Quota-Remaining": quotaHeader } : {}),
    },
  })
}

// Transforms one raw SSE event from the backend into the event forwarded to the
// browser. Returns null for events with no data payload. Citation events are
// re-normalised (snake_case → camelCased Citation); every other event type
// (text-delta, personal-data-flag, summary-update, thread-continuation,
// calendar-action, …) is forwarded unchanged.
function relaySseEvent(rawEvent: string): string | null {
  const data = rawEvent
    .split("\n")
    .filter((line) => line.startsWith("data:"))
    .map((line) => line.slice(5).replace(/^ /, ""))
    .join("\n")

  if (!data) return null
  if (data === "[DONE]") return "data: [DONE]\n\n"

  let parsed: unknown
  try {
    parsed = JSON.parse(data)
  } catch {
    // Unrecognised payload — forward verbatim rather than dropping it.
    return `data: ${data}\n\n`
  }

  if (
    parsed &&
    typeof parsed === "object" &&
    (parsed as { type?: unknown }).type === "citations"
  ) {
    const raw = (parsed as { citations?: unknown[] }).citations ?? []
    const citations = raw
      .map((c) => normaliseSource(c as Parameters<typeof normaliseSource>[0]))
      .filter((c): c is NonNullable<ReturnType<typeof normaliseSource>> => c !== null)
    return sseLine({ type: "citations", citations })
  }

  return sseLine(parsed)
}
