import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> },
) {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return NextResponse.json({ error: "Forbidden: Admin access required" }, { status: 403 })
  }

  const { id } = await params
  if (!/^\d+$/.test(id)) {
    return NextResponse.json({ error: "Invalid report id" }, { status: 400 })
  }

  const internalToken = signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl(`/bug-report/admin/${id}/screenshot`), {
      headers: { Authorization: `Bearer ${internalToken}` },
      cache: "no-store",
    })
  } catch (err) {
    console.error("[admin API] fetch bug report screenshot error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }

  if (!backendRes.ok || !backendRes.body) {
    return NextResponse.json(
      { error: backendRes.status === 404 ? "Screenshot not found" : "Failed to fetch screenshot" },
      { status: backendRes.status >= 500 ? 502 : backendRes.status },
    )
  }

  // Stream the image bytes straight through — never buffer/re-encode.
  return new NextResponse(backendRes.body, {
    status: 200,
    headers: {
      "Content-Type": backendRes.headers.get("Content-Type") ?? "application/octet-stream",
      "Cache-Control": "private, max-age=300",
    },
  })
}
