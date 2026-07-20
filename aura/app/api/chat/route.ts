import { getServerSession } from "next-auth"
import { z } from "zod"

import {
  backendUrl,
  type BackendChatRequest,
  type BackendChatResponse,
} from "@/lib/api/backend"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export const maxDuration = 60

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
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId || !session.user.role) {
    return new Response("Unauthorized", { status: 401 })
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

  const internalToken = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

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

  let data: BackendChatResponse
  try {
    data = (await backendRes.json()) as BackendChatResponse
  } catch {
    return new Response("Invalid backend response", { status: 502 })
  }

  const answer = data?.answer ?? ""
  const isPersonalData = data?.is_personal_data === true
  const citations = (data?.sources ?? [])
    .map(normaliseSource)
    .filter((c): c is NonNullable<ReturnType<typeof normaliseSource>> => c !== null)

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
      controller.enqueue(encoder.encode("data: [DONE]\n\n"))
      controller.close()
    },
  })

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  })
}
