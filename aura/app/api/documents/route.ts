import { getServerSession } from "next-auth"
import { NextResponse } from "next/server"
import { cookies } from "next/headers"
import { randomUUID } from "crypto"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

function isSafeDocumentPath(path: string): boolean {
  if (path.includes("\0")) return false
  if (path.includes("\\")) return false
  if (path.startsWith("/")) return false
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(path)) return false
  if (path.split("/").some((segment) => segment === "..")) return false
  return /^[A-Za-z0-9._/-]+$/.test(path)
}

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)

  let role = "guest"
  let erpId = ""
  let department, email, fullName, currentYear, currentSem, currentSec
  let newGuestId: string | undefined = undefined

  if (session?.user?.erpId && session.user.role) {
    role = session.user.role
    erpId = session.user.erpId
    department = session.user.department
    email = session.user.email ?? undefined
    fullName = session.user.fullName
    currentYear = session.user.currentYear
    currentSem = session.user.currentSem
    currentSec = session.user.currentSec
  } else {
    // If no session exists, check for the guest cookie.
    // If missing, generate one now so they aren't blocked.
    const cookieStore = await cookies()
    let guestId = cookieStore.get("aura-guest-id")?.value

    if (!guestId || guestId.length > 64) {
      guestId = `GUEST-${randomUUID()}`
      newGuestId = guestId // Flag to attach this cookie to the response
    }
    erpId = guestId
  }

  // Helper to attach the guest cookie to outgoing responses if we just minted it
  const sendResponse = (res: NextResponse) => {
    if (newGuestId) {
      res.cookies.set("aura-guest-id", newGuestId, {
        httpOnly: true,
        sameSite: "lax",
        secure: process.env.NODE_ENV === "production",
        path: "/",
        maxAge: 60 * 60 * 24 * 365,
      })
    }
    return res
  }

  const { searchParams } = new URL(req.url)
  const path = searchParams.get("path")?.trim()

  if (!path) {
    return sendResponse(NextResponse.json({ error: "Missing path" }, { status: 400 }))
  }
  if (!isSafeDocumentPath(path)) {
    return sendResponse(NextResponse.json({ error: "Invalid path" }, { status: 400 }))
  }

  const token = signInternalJwt({
    role,
    erpId,
    department,
    email,
    fullName,
    currentYear,
    currentSem,
    currentSec,
  })

  try {
    const res = await fetch(backendUrl(`/documents/${path.split("/").map(encodeURIComponent).join("/")}`), {
      method: "GET",
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return sendResponse(NextResponse.json({ error: "Failed to fetch document" }, { status: res.status }))
      }
      let errDetail = "Failed to fetch document"
      try {
        const errJson = await res.json()
        if (errJson?.detail) errDetail = errJson.detail
      } catch {
        // ignore parse failure
      }
      return sendResponse(NextResponse.json({ error: errDetail }, { status: res.status }))
    }

    const data = await res.json()
    return sendResponse(NextResponse.json(data))
  } catch (err) {
    console.error("[documents] GET failed:", err)
    return sendResponse(NextResponse.json({ error: "Backend unavailable" }, { status: 502 }))
  }
}