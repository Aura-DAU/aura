import { z } from "zod"
import { backendUrl, type BackendChatRequest } from "@/lib/api/backend"

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

export async function POST(req: Request) {
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

  const authHeader = req.headers.get("Authorization")
  if (!authHeader) {
    return new Response("Unauthorized", { status: 401 })
  }

  // Map studentProfile → userProfile for FastAPI; cap history for cost/latency.
  const payload: BackendChatRequest = {
    question: parsed.data.question,
    history: parsed.data.history?.slice(-6),
    studentProfile: parsed.data.studentProfile,
  }

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/chat/stream"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: authHeader,
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

  if (!backendRes.ok || !backendRes.body) {
    const text = await backendRes.text().catch(() => "")
    console.error("[chat] backend error:", backendRes.status, text)
    return new Response("Backend error", { status: 502 })
  }

  // The backend emits the exact SSE events the client parses
  // (text-delta / citations / personal-data-flag / [DONE]) — pipe it through
  // so tokens reach the browser as they are generated.
  return new Response(backendRes.body, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  })
}
