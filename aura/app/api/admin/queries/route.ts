import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return NextResponse.json({ error: "Forbidden: Admin access required" }, { status: 403 })
  }

  const { searchParams } = new URL(req.url)
  const forwardParams = new URLSearchParams()

  for (const [key, val] of searchParams.entries()) {
    if (val !== undefined && val !== null && val !== "") {
      forwardParams.set(key, val)
    }
  }

  const internalToken = await signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  try {
    const res = await fetch(backendUrl(`/admin/queries?${forwardParams.toString()}`), {
      headers: {
        Authorization: `Bearer ${internalToken}`,
      },
      cache: "no-store",
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to fetch query traces" }, { status: res.status })
      }
      const errText = await res.text().catch(() => "")
      return NextResponse.json({ error: errText || "Failed to fetch query traces" }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[admin API] fetch query traces error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
