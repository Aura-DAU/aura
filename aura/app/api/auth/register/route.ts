import { saveUser } from "@/lib/db/user-db"
import { NextResponse } from "next/server"
import { z } from "zod"

const registerSchema = z.object({
  name: z.string().trim().min(1, "Full name is required"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  role: z.enum(["student", "parent"])
})

export async function POST(req: Request) {
  let body: unknown
  try { body = await req.json() } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = registerSchema.safeParse(body)
  if (!parsed.success) {
    return NextResponse.json({ error: parsed.error.issues[0]?.message || "Invalid input" }, { status: 400 })
  }

  const { name, email, password, role } = parsed.data

  if (role === "student" && !email.toLowerCase().endsWith("@dau.ac.in")) {
    return NextResponse.json(
      { error: "Student email must end with @dau.ac.in" },
      { status: 400 }
    )
  }

  try {
    await saveUser({ name, email, password, role })
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
