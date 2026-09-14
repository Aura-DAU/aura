import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

function forbidden() {
  return NextResponse.json({ error: "Forbidden: Admin access required" }, { status: 403 })
}

/** Prefer FastAPI's `detail` field over the raw JSON body for client toasts. */
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

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return forbidden()
  }

  const { searchParams } = new URL(req.url)
  const status = searchParams.get("status")
  const category = searchParams.get("category")
  const limit = searchParams.get("limit") ?? "100"
  const offset = searchParams.get("offset") ?? "0"

  const qs = new URLSearchParams()
  if (status) qs.set("status", status)
  if (category) qs.set("category", category)
  qs.set("limit", limit)
  qs.set("offset", offset)

  const internalToken = signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  try {
    const res = await fetch(backendUrl(`/bug-report/admin/list?${qs.toString()}`), {
      headers: { Authorization: `Bearer ${internalToken}` },
      cache: "no-store",
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to fetch bug reports" }, { status: res.status })
      }
      return NextResponse.json(
        { error: await backendErrorMessage(res, "Failed to fetch bug reports") },
        { status: res.status },
      )
    }

    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[admin API] fetch bug reports error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
