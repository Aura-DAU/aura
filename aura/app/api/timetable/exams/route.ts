import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextRequest, NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export async function GET(request: NextRequest) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)
  const limit = searchParams.get("limit") ?? "5"

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
    const res = await fetch(backendUrl(`/timetable/me/exams?limit=${limit}`), {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to fetch exam schedule" }, { status: res.status })
      }
      let detail = "Failed to fetch exam schedule"
      try {
        const j = await res.json()
        if (j?.detail) detail = j.detail
      } catch { /* ignore */ }
      return NextResponse.json({ error: detail }, { status: res.status })
    }

    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[timetable/exams] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
