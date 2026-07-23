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
  })
}

export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const body = await request.json()
    const res = await fetch(backendUrl("/push/subscribe"), {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to subscribe" }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[push/subscribe] POST failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function DELETE(request: NextRequest) {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(request.url)
  const endpoint = searchParams.get("endpoint")
  if (!endpoint) {
    return NextResponse.json({ error: "Missing endpoint parameter" }, { status: 400 })
  }

  try {
    const res = await fetch(
      backendUrl(`/push/subscribe?endpoint=${encodeURIComponent(endpoint)}`),
      {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${token}` },
      },
    )
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to unsubscribe" }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[push/subscribe] DELETE failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
