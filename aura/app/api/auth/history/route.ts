import { getServerSession } from "next-auth"
import { NextResponse } from "next/server"
import { z } from "zod"

import { authOptions } from "@/lib/auth/options"
import { saveThreadsForUser } from "@/lib/db/chat-db"

const historySchema = z.object({
  // email in the body is ignored — persistence is bound to the session.
  email: z.string().email().optional(),
  threads: z.array(z.any()),
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
    await saveThreadsForUser(sessionEmail, parsed.data.threads)
    return NextResponse.json({ ok: true })
  } catch (err) {
    console.error("[history]", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
