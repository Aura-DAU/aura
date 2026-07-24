import { getServerSession } from "next-auth"
import { z } from "zod"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

// Shape of a standard browser PushSubscription (subscription.toJSON()) plus the
// UA string the client attaches. Validated so we never forward unbounded input.
const subscribeSchema = z.object({
  endpoint: z.string().min(1).max(2048).url(),
  keys: z.object({
    p256dh: z.string().min(1).max(256),
    auth: z.string().min(1).max(256),
  }),
  user_agent: z.string().max(1024).optional(),
})

interface SessionWithUser {
  user: {
    role: "student" | "faculty" | "admin" | "guest"
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
    fullName: session.user.fullName ?? undefined,
    currentYear: session.user.currentYear ?? undefined,
    currentSem: session.user.currentSem ?? undefined,
    currentSec: session.user.currentSec ?? undefined,
  })
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  let rawBody: unknown
  try {
    rawBody = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = subscribeSchema.safeParse(rawBody)
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid subscription payload" }, { status: 400 })
  }
  const body = parsed.data

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
      // Do not forward raw backend 5xx bodies — they can leak internals.
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to subscribe" }, { status: res.status })
      }
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
  if (endpoint.length > 2048) {
    return NextResponse.json({ error: "Invalid endpoint" }, { status: 400 })
  }

  try {
    const res = await fetch(backendUrl(`/push/subscribe?endpoint=${encodeURIComponent(endpoint)}`), {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${buildToken(session as unknown as SessionWithUser)}` },
    })

    if (!res.ok) {
      // Do not forward raw backend 5xx bodies — they can leak internals.
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to unsubscribe" }, { status: res.status })
      }
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
