import { getServerSession, type Session } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

function buildToken(session: Session | null) {
  if (!session?.user?.erpId) return null
  return signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
  })
}

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(req.url)
  const date = searchParams.get("date")
  if (!date) {
    return NextResponse.json({ error: "date query param is required (YYYY-MM-DD)" }, { status: 400 })
  }

  try {
    const res = await fetch(backendUrl(`/calendar/meetings?date=${encodeURIComponent(date)}`), {
      headers: { "Authorization": `Bearer ${token}` },
      cache: "no-store",
    })
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to fetch calendar meetings" }, { status: res.status })
    }
    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[calendar/meetings] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
