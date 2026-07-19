import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

interface SessionWithUser {
  user: {
    role: string
    erpId: string
    department: string
    email?: string | null
    fullName?: string | null
    currentYear?: number | null
    currentSem?: number | null
    currentSec?: string | null
  }
}

function buildToken(session: SessionWithUser) {
  return signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
  })
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  let body
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  try {
    const res = await fetch(backendUrl("/push/subscribe"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${buildToken(session as unknown as SessionWithUser)}`,
      },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      const errText = await res.text().catch(() => "")
      return NextResponse.json({ error: errText || "Failed to subscribe" }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[push/subscribe] POST failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function DELETE(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(req.url)
  const endpoint = searchParams.get("endpoint")
  if (!endpoint) {
    return NextResponse.json({ error: "endpoint query param is required" }, { status: 400 })
  }

  try {
    const res = await fetch(backendUrl(`/push/subscribe?endpoint=${encodeURIComponent(endpoint)}`), {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${buildToken(session as unknown as SessionWithUser)}` },
    })

    if (!res.ok) {
      const errText = await res.text().catch(() => "")
      return NextResponse.json({ error: errText || "Failed to unsubscribe" }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[push/subscribe] DELETE failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
