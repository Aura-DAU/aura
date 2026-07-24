import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const token = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
  })

  try {
    // Backend returns a RedirectResponse to Google's OAuth consent screen.
    // We fetch it without following redirects, then return the redirect URL
    // as JSON so the frontend can do a full-page navigation.
    const res = await fetch(backendUrl("/calendar/connect"), {
      headers: { "Authorization": `Bearer ${token}` },
      redirect: "manual",
    })

    if (res.status === 307 || res.status === 302 || res.status === 301) {
      const url = res.headers.get("location")
      return NextResponse.json({ url })
    }

    // Non-redirect response is an error
    let errDetail = "Failed to start calendar connection"
    try {
      const errJson = await res.json()
      if (errJson?.detail) errDetail = errJson.detail
    } catch {
      // ignore
    }
    return NextResponse.json({ error: errDetail }, { status: res.status })
  } catch (err) {
    console.error("[calendar/connect] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
