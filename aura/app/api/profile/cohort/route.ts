import { getServerSession, type Session } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextRequest, NextResponse } from "next/server"
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

export async function GET() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/profile/cohort"), {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` },
      cache: "no-store",
    })

    if (!res.ok) {
      let errDetail = "Failed to fetch cohort profile"
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
    console.error("[profile/cohort] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const body = await request.json()
    const res = await fetch(backendUrl("/profile/cohort"), {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      let errDetail = "Failed to save cohort profile"
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
    console.error("[profile/cohort] POST failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
