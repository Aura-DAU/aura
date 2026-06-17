import { saveUser } from "@/lib/db/user-db"
import { NextResponse } from "next/server"

export async function POST(req: Request) {
  let body: unknown
  try { body = await req.json() } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const { name, email, password, role } = body as Record<string, string>

  if (!name || !email || !password || !role) {
    return NextResponse.json({ error: "All fields are required" }, { status: 400 })
  }
  if (role !== "student" && role !== "parent") {
    return NextResponse.json({ error: "Invalid role" }, { status: 400 })
  }
  if (role === "student" && !email.toLowerCase().endsWith("@dau.ac.in")) {
    return NextResponse.json(
      { error: "Student email must end with @dau.ac.in" },
      { status: 400 }
    )
  }
  if (password.length < 8) {
    return NextResponse.json(
      { error: "Password must be at least 8 characters" },
      { status: 400 }
    )
  }

  try {
    await saveUser({ name, email, password, role: role as "student" | "parent" })
    return NextResponse.json({ name, email, role }, { status: 201 })
  } catch (err) {
    if (err instanceof Error && err.message === "USER_EXISTS") {
      return NextResponse.json(
        { error: "An account with this email already exists" },
        { status: 409 }
      )
    }
    console.error("[register]", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }
}
