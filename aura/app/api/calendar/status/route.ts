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
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
  })
}

export async function GET() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/calendar/status"), {
      headers: { "Authorization": `Bearer ${token}` },
      cache: "no-store",
    })
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to check calendar status" }, { status: res.status })
    }
    const data = await res.json()
    // The backend already computes can_sync_timetable from the actual
    // granted OAuth scope (linked alone isn't enough — a readonly grant
    // is still "linked" but can't sync). Relay it as-is rather than
    // re-deriving it here from `linked`, which would say "yes" even when
    // the backend would reject the sync.
    return NextResponse.json(data)
  } catch (err) {
    console.error("[calendar/status] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
