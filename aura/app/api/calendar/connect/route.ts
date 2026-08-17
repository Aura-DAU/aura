import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextRequest, NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

const ALLOWED_RETURN_TO = new Set(["/", "/dashboard", "/settings/calendar"])

export async function GET(req: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const token = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
    currentLabGroup: session.user.currentLabGroup,
  })

  const requested = req.nextUrl.searchParams.get("return_to") ?? "/dashboard"
  const returnTo = ALLOWED_RETURN_TO.has(requested) ? requested : "/dashboard"

  try {
    // Backend returns JSON {"url": "..."} pointing at Google's OAuth consent
    // screen — it can't 307 to an external host that fetch() would follow —
    // so we forward that URL and the frontend does a full-page navigation.
    const res = await fetch(
      backendUrl(`/calendar/connect?return_to=${encodeURIComponent(returnTo)}`),
      {
        headers: { Authorization: `Bearer ${token}` },
      },
    )

    const data = await res.json().catch(() => null)

    if (res.ok && data?.url) {
      return NextResponse.json({ url: data.url })
    }

    const errDetail = data?.detail || "Failed to start calendar connection"
    return NextResponse.json({ error: errDetail }, { status: res.ok ? 502 : res.status })
  } catch (err) {
    console.error("[calendar/connect] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
