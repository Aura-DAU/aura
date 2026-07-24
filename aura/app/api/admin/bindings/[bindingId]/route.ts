import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ bindingId: string }> }
) {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return NextResponse.json({ error: "Forbidden: Admin access required" }, { status: 403 })
  }

  const { bindingId } = await params

  const internalToken = await signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  try {
    const res = await fetch(backendUrl(`/admin/bindings/${bindingId}`), {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${internalToken}`,
      },
    })

    if (!res.ok) {
      // Do not forward raw backend 5xx bodies — they can leak internals.
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to revoke binding" }, { status: res.status })
      }
      const errText = await res.text().catch(() => "")
      return NextResponse.json({ error: errText || "Failed to revoke binding" }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[admin API] delete error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}