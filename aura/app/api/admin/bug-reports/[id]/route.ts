import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { z } from "zod"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

const updateStatusSchema = z.object({
  status: z.enum(["open", "in_progress", "resolved"]),
})

async function backendErrorMessage(res: Response, fallback: string): Promise<string> {
  const errText = await res.text().catch(() => "")
  if (!errText) return fallback
  try {
    const parsed = JSON.parse(errText) as { detail?: unknown; error?: unknown }
    if (typeof parsed.detail === "string" && parsed.detail.trim()) return parsed.detail
    if (typeof parsed.error === "string" && parsed.error.trim()) return parsed.error
  } catch {
    // Non-JSON backend body — return as-is.
  }
  return errText
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return NextResponse.json({ error: "Forbidden: Admin access required" }, { status: 403 })
  }

  const { id } = await params
  if (!/^\d+$/.test(id)) {
    return NextResponse.json({ error: "Invalid report id" }, { status: 400 })
  }

  let rawBody: unknown
  try {
    rawBody = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = updateStatusSchema.safeParse(rawBody)
  if (!parsed.success) {
    return NextResponse.json({ error: "status must be one of open, in_progress, resolved" }, { status: 400 })
  }

  const internalToken = signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  try {
    const res = await fetch(backendUrl(`/bug-report/admin/${id}`), {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${internalToken}`,
      },
      body: JSON.stringify(parsed.data),
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to update bug report" }, { status: res.status })
      }
      return NextResponse.json(
        { error: await backendErrorMessage(res, "Failed to update bug report") },
        { status: res.status },
      )
    }

    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[admin API] update bug report status error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
