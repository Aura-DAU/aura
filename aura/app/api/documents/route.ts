import { getServerSession } from "next-auth"
import { NextResponse } from "next/server"
import { cookies } from "next/headers"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"
import {
  readOrMintGuestCookies,
  guestErpId,
  guestCookieOptions,
  GUEST_ID_COOKIE,
  GUEST_SECRET_COOKIE,
} from "@/lib/auth/guest-identity"

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

  let role: "student" | "faculty" | "admin" | "guest" = "guest"
  let erpId = ""
  let department, email, fullName, currentYear, currentSem, currentSec
  let newGuestId: string | undefined = undefined
  let newGuestSecret: string | undefined = undefined

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
    const guestCookies = readOrMintGuestCookies(cookieStore)
    if (guestCookies.isNew) {
      newGuestId = guestCookies.guestId
      newGuestSecret = guestCookies.guestSecret
    }
    erpId = guestErpId(guestCookies)
  }

  // Helper to attach the guest cookies to outgoing responses if we just minted them
  const sendResponse = (res: NextResponse) => {
    if (newGuestId && newGuestSecret) {
      const opts = guestCookieOptions()
      res.cookies.set(GUEST_ID_COOKIE, newGuestId, opts)
      res.cookies.set(GUEST_SECRET_COOKIE, newGuestSecret, opts)
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