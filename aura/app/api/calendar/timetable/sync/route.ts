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

export async function POST() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/calendar/timetable/sync"), {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
    })
    if (!res.ok) {
      let errDetail = "Failed to sync timetable"
      try {
        const errJson = await res.json()
        if (errJson?.detail) errDetail = errJson.detail
      } catch {
        // ignore
      }
      return NextResponse.json({ error: errDetail }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[calendar/timetable/sync] POST failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function DELETE() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/calendar/timetable/sync"), {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` },
    })
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to unsync timetable" }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[calendar/timetable/sync] DELETE failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
