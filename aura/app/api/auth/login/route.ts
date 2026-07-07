import { findUser, verifyPassword } from "@/lib/db/user-db"
import { getThreadsForUser } from "@/lib/db/chat-db"
import { NextResponse } from "next/server"
import { z } from "zod"

const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(1, "Password is required"),
  role: z.enum(["student", "parent", "faculty"])
})

export async function POST(req: Request) {
  let body: unknown
  try { body = await req.json() } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = loginSchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message || "Invalid input" }, { status: 400 })
  }

  const { email, password, role } = parsed.data

  const user = await findUser(email, role)
  if (!user || !verifyPassword(password, user.passwordHash)) {
    return NextResponse.json({ error: "Invalid email or password" }, { status: 401 })
  }

  // Fetch stored thread history for this user
  const threads = await getThreadsForUser(email)

  return NextResponse.json(
    { name: user.name, email: user.email, role: user.role, threads },
    { status: 200 }
  )
}
