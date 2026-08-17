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
    currentLabGroup: session.user.currentLabGroup,
  })
}

export async function DELETE() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/calendar/disconnect"), {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` },
    })
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to disconnect calendar" }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[calendar/disconnect] DELETE failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
