import { saveThreadsForUser } from "@/lib/db/chat-db"
import { NextResponse } from "next/server"
import { z } from "zod"

const historySchema = z.object({
  email: z.string().email("Invalid email address"),
  threads: z.array(z.any())
})

export async function POST(req: Request) {
  let body: unknown
  try { body = await req.json() } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = historySchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message || "Invalid input" }, { status: 400 })
  }

  const { email, threads } = parsed.data

  try {
    await saveThreadsForUser(email, threads)
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error("[history]", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
