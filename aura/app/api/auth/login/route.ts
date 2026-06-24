import { findUser, verifyPassword } from "@/lib/db/user-db"
import { getThreadsForUser } from "@/lib/db/chat-db"
import { NextResponse } from "next/server"

export async function POST(req: Request) {
  let body: unknown
  try { body = await req.json() } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const { email, password, role } = body as Record<string, string>

  if (!email || !password || !role) {
    return NextResponse.json({ error: "All fields are required" }, { status: 400 })
  }
  if (role !== "student" && role !== "parent" && role !== "faculty") {
    return NextResponse.json({ error: "Invalid role" }, { status: 400 })
  }

  const user = await findUser(email, role as "student" | "parent" | "faculty")
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
