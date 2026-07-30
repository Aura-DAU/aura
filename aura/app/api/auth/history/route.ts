import { getServerSession } from "next-auth"
import { NextResponse } from "next/server"
import { z } from "zod"

import { authOptions } from "@/lib/auth/options"
import { saveThreadsForUser } from "@/lib/db/chat-db"

const MAX_THREADS = 10
const MAX_MESSAGES_PER_THREAD = 100

const historyMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().max(20_000),
  timestamp: z.number().optional(),
  is_personal_data: z.boolean().optional(),
  calendar_action: z
    .object({
      event_title: z.string().max(500).optional(),
      date: z.string().max(64).optional(),
      time: z.string().max(64).optional(),
      attendees: z.array(z.string().max(256)).max(50).optional(),
      status: z.enum(["confirmed", "pending", "failed"]).optional(),
      calendar_link: z.string().max(2048).optional(),
      description: z.string().max(2000).optional(),
    })
    .optional(),
})

const historyThreadSchema = z.object({
  id: z.string().min(1).max(128),
  title: z.string().max(500),
  messages: z.array(historyMessageSchema).max(MAX_MESSAGES_PER_THREAD),
  // Recency + rolling-memory fields — previously stripped by Zod, so the
  // sidebar never got updatedAt from the server and summary was lost on sync.
  updatedAt: z.number().optional(),
  summary: z.string().max(20_000).optional(),
  summaryTurnCount: z.number().int().min(0).optional(),
  continuedFromId: z.string().min(1).max(128).optional(),
})

const historySchema = z.object({
  // email in the body is ignored — persistence is bound to the session.
  email: z.string().email().max(320).optional(),
  threads: z.array(historyThreadSchema).max(MAX_THREADS),
  /** Client watermark so out-of-order POSTs cannot overwrite newer history. */
  clientSyncAt: z.number().optional(),
})

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  const sessionEmail = session?.user?.email
  if (!sessionEmail) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  let body: unknown
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = historySchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json(
      { error: parsed.error.issues[0]?.message || "Invalid input" },
      { status: 400 },
    )
  }

  try {
    const result = await saveThreadsForUser(
      sessionEmail,
      parsed.data.threads,
      parsed.data.clientSyncAt,
    )
    if (!result.ok) {
      return NextResponse.json({ ok: false, reason: result.reason }, { status: 409 })
    }
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error("[history]", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}

export async function GET() {
  const session = await getServerSession(authOptions)
  const sessionEmail = session?.user?.email
  if (!sessionEmail) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const { getThreadsForUser } = await import("@/lib/db/chat-db")
    const threads = await getThreadsForUser(sessionEmail)
    return NextResponse.json({ threads })
  } catch (err) {
    console.error("[history GET]", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
