/**
 * GET /api/erp/cgpa
 * Returns the authenticated student's current CGPA from the ERP DB.
 * Called by StudentDashboard on mount.
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

  const res = await fetch(backendUrl(`/erp/student/cgpa?erp_id=${session.user.erpId}`), {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  })

  if (!res.ok) {
    return NextResponse.json({ error: "Failed to fetch CGPA" }, { status: res.status })
  }

  return NextResponse.json(await res.json())
}
