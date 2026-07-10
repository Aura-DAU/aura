/**
 * GET /api/erp/timetable
 * Returns the authenticated student's full weekly timetable from the ERP DB.
 * Client-side filtering to today's day is done in StudentDashboard.
 */
import { getServerSession } from "next-auth"
import { authOptions }      from "@/lib/auth/options"
import { backendUrl }       from "@/lib/api/backend"
import { NextResponse }     from "next/server"
import { signInternalJwt }  from "@/lib/auth/internal-jwt"

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId || session.user.role === "guest") {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const token = signInternalJwt({
    role:       session.user.role,
    erpId:      session.user.erpId,
    department: session.user.department,
  })

  const res = await fetch(backendUrl(`/erp/student/timetable?erp_id=${session.user.erpId}`), {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })

  if (!res.ok) {
    return NextResponse.json({ error: "Failed to fetch timetable" }, { status: res.status })
  }

  return NextResponse.json(await res.json())
}
