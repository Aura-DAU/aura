import { getServerSession } from "next-auth"
import { cookies } from "next/headers"
import { randomUUID } from "crypto"
import { z } from "zod"

import {
  backendUrl,
  type BackendChatRequest,
  type BackendChatResponse,
} from "@/lib/api/backend"
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

  // Map studentProfile → userProfile for FastAPI; cap history for cost/latency.
  const payload: BackendChatRequest = {
    question: parsed.data.question,
    history: parsed.data.history?.slice(-6),
    studentProfile: parsed.data.studentProfile,
  }

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/chat"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${internalToken}`,
      },
      body: JSON.stringify({
        question: payload.question,
        history: payload.history,
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
    return new Response("Backend error", { status: 502 })
  }

  const rawBody = await backendRes.text()
  let data: BackendChatResponse
  try {
    data = JSON.parse(rawBody) as BackendChatResponse
  } catch {
    console.error(
      "[chat] backend returned non-JSON:",
      backendRes.status,
      rawBody.slice(0, 200),
    )
    return new Response("Invalid backend response", { status: 502 })
  }

  const answer = data?.answer ?? ""
  const isPersonalData = data?.is_personal_data === true
  const citations = (data?.sources ?? [])
    .map(normaliseSource)
    .filter((c): c is NonNullable<ReturnType<typeof normaliseSource>> => c !== null)
  // Server-authoritative remaining count (undefined/null for unlimited
  // @dau.ac.in roles). Forwarded to the client so its counter can never
  // drift from what the backend will actually enforce next time.
  const quotaRemaining = typeof data?.quota_remaining === "number" ? data.quota_remaining : null

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const encoder = new TextEncoder()
      controller.enqueue(encoder.encode(sseLine({ type: "text-delta", delta: answer })))
      if (citations.length > 0) {
        controller.enqueue(encoder.encode(sseLine({ type: "citations", citations })))
      }
      if (isPersonalData) {
        controller.enqueue(encoder.encode(sseLine({ type: "personal-data-flag" })))
      }
      if (quotaRemaining !== null) {
        controller.enqueue(encoder.encode(sseLine({ type: "quota", remaining: quotaRemaining })))
      }
      controller.enqueue(encoder.encode("data: [DONE]\n\n"))
      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
      ...(quotaRemaining !== null ? { "X-Quota-Remaining": String(quotaRemaining) } : {}),
    },
  })
}
