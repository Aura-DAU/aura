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
    email: session.user.email ?? undefined,
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
    const res = await fetch(backendUrl("/timetable/me/changes"), {
      method: "GET",
      headers: { "Authorization": `Bearer ${token}` },
      cache: "no-store",
    })

    if (!res.ok) {
      // Do not forward raw backend 5xx bodies — they can leak internals.
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to fetch timetable changes" }, { status: res.status })
      }
      const errText = await res.text().catch(() => "")
      return NextResponse.json({ error: errText || "Failed to fetch timetable changes" }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[timetable/changes] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

/** Add/replace/remove one entry on the caller's own timetable — the
 * dashboard's counterpart to asking AURA in chat. See
 * server/api/routes/timetable_routes.py::add_my_timetable_change for why
 * this can write straight through with no separate confirm step: the
 * dashboard form submit already is the confirmation. */
export async function POST(request: NextRequest) {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const body = await request.json()
    const res = await fetch(backendUrl("/timetable/me/changes"), {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!res.ok) {
      let errDetail = "Failed to save timetable change"
      try {
        const errJson = await res.json()
        if (errJson?.detail) errDetail = errJson.detail
      } catch {
        // ignore parse failure
      }
      return NextResponse.json({ error: errDetail }, { status: res.status })
    }

    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[timetable/changes] POST failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
