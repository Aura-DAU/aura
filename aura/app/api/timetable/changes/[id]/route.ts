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
    email: session.user.email ?? undefined,
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
    currentLabGroup: session.user.currentLabGroup,
  })
}

/** Remove one of the caller's own timetable overrides — dashboard
 * counterpart to the chat undo_timetable_change tool. The backend scopes
 * the delete to the caller's own erp_id, so the `id` in the path can only
 * ever affect the signed-in student's own timetable. */
export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { id } = await params

  try {
    const res = await fetch(backendUrl(`/timetable/me/changes/${encodeURIComponent(id)}`), {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` },
    })

    if (!res.ok) {
      let errDetail = "Failed to remove timetable change"
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
    console.error("[timetable/changes/:id] DELETE failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
