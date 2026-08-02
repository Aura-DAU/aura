import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
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
    const res = await fetch(backendUrl("/timetable/me"), {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` },
      cache: "no-store",
    })

    if (!res.ok) {
      // Do not forward raw backend 5xx bodies — they can leak internals.
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to fetch timetable" }, { status: res.status })
      }
      let errDetail = "Failed to fetch timetable"
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
    console.error("[timetable/me] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
