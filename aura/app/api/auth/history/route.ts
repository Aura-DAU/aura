import { saveThreadsForUser, type StoredThread } from "@/lib/db/chat-db"
import { NextResponse } from "next/server"

export async function POST(req: Request) {
  let body: unknown
  try { body = await req.json() } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const { email, threads } = body as { email?: string; threads?: StoredThread[] }

  if (!email || !Array.isArray(threads)) {
    return NextResponse.json({ error: "email and threads are required" }, { status: 400 })
  }

  try {
    await saveThreadsForUser(email, threads)
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error("[history]", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
