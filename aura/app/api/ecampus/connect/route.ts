import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { NextResponse } from "next/server"
// import { backendUrl } from "@/lib/api/backend" // uncomment when backend is ready

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  
  if (!session?.user) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  let body
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const { password } = body
  if (!password) {
    return NextResponse.json({ error: "Password is required" }, { status: 400 })
  }

  // Mint internal JWT
  const internalToken = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
  })

  // DUMMY IMPLEMENTATION for unbuilt backend
  // In the future, this will be:
  // const backendRes = await fetch(backendUrl("/ecampus/credentials"), { ... })
  console.log(`[DUMMY] Forwarding eCampus credentials for ${session.user.erpId} to backend with token: ${internalToken.substring(0, 10)}...`)
  
  // Fake delay
  await new Promise(resolve => setTimeout(resolve, 800))

  return NextResponse.json({ success: true })
}
