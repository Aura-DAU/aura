import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { getRemainingQuota } from "@/lib/db/rate-limit-db"
import { NextResponse } from "next/server"

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session?.user?.id) {
    return new NextResponse("Unauthorized", { status: 401 })
  }

  const sub = session.user.id
  const role = session.user.role || "guest"
  
  try {
    const remaining = await getRemainingQuota(sub, role)
    return NextResponse.json({ remaining })
  } catch (err) {
    console.error("[quota] Failed to retrieve quota:", err)
    return new NextResponse("Internal Server Error", { status: 500 })
  }
}
