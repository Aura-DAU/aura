import { getServerSession } from "next-auth"
import { NextResponse } from "next/server"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

// Phase C (FE-3/BE-2): backs the citation side-drawer. Given a citation's
// `path` (the relative markdown path returned alongside a citation, e.g.
// "infrastructure/ict_infrastructure.md"), fetches the raw source from
// FastAPI's /documents endpoint so it can be rendered and scrolled/
// highlighted to the cited line range in ChatShell's drawer.
export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(req.url)
  const path = searchParams.get("path")?.trim()
  if (!path) {
    return NextResponse.json({ error: "Missing path" }, { status: 400 })
  }

  const token = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
  })

  try {
    const res = await fetch(backendUrl(`/documents/${path.split("/").map(encodeURIComponent).join("/")}`), {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })

    if (!res.ok) {
      let errDetail = "Failed to fetch document"
      try {
        const errJson = await res.json()
        if (errJson?.detail) errDetail = errJson.detail
      } catch {
        // ignore parse failure, use default message
      }
      return NextResponse.json({ error: errDetail }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[documents] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
