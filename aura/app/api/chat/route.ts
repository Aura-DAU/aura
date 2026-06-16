import { z } from "zod"
import {
  backendUrl,
  type BackendChatRequest,
  type BackendChatResponse,
} from "@/lib/api/backend"

export const maxDuration = 60

const historyTurnSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string(),
})

const studentProfileSchema = z.object({
  name: z.string().optional(),
  branch: z.string().optional(),
  year: z.string().optional(),
  semester: z.string().optional(),
  interests: z.string().optional(),
})

const requestSchema = z.object({
  question: z.string().min(1, "question is required"),
  history: z.array(historyTurnSchema).optional(),
  studentProfile: studentProfileSchema.optional(),
})

function sseLine(data: unknown): string {
  return `data: ${JSON.stringify(data)}\n\n`
}

function normaliseSource(s: string | { file?: string; title?: string }): {
  file: string
  title?: string
} | null {
  if (typeof s === "string") return { file: s }
  if (s && typeof s === "object" && s.file) return { file: s.file, title: s.title }
  return null
}

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

  const payload: BackendChatRequest = parsed.data

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/chat"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
  } catch (err) {
    console.error("[chat] backend unreachable:", err)
    return new Response("Backend unavailable", { status: 502 })
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
  const citations = (data?.sources ?? [])
    .map(normaliseSource)
    .filter((c): c is { file: string; title?: string } => c !== null)

  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const encoder = new TextEncoder()
      controller.enqueue(encoder.encode(sseLine({ type: "text-delta", delta: answer })))
      if (citations.length > 0) {
        controller.enqueue(encoder.encode(sseLine({ type: "citations", citations })))
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
