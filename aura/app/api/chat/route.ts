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

function normaliseSource(s: string | { file?: string; url?: string; title?: string; start_line?: number; end_line?: number; document_year?: string }): {
  file: string
  title?: string
  start_line?: number
  end_line?: number
  document_year?: string
} | null {
  if (typeof s === "string") return { file: s }
  if (s && typeof s === "object") {
    const file = s.file || s.url || ""
    if (file) {
      return {
        file,
        title: s.title,
        start_line: s.start_line,
        end_line: s.end_line,
        document_year: s.document_year,
      }
    }
  }
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

  const authHeader = req.headers.get("Authorization")
  if (!authHeader) {
    return new Response("Unauthorized", { status: 401 })
  }

  // studentProfileSchema has no role field — identity comes from the JWT only.
  const payload: BackendChatRequest = parsed.data

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/chat"), {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        "Authorization": authHeader
      },
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
  const isPersonalData = data?.is_personal_data === true
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
