import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { getToken } from "next-auth/jwt"

import { getNextAuthSecret } from "@/lib/auth/secrets"

const PUBLIC_PATHS = ["/login", "/api/auth", "/_next", "/favicon.ico", "/offline"]
// Anonymous guest chat (#206): /api/chat mints its own guest JWT + cookie
// quota key. Must stay reachable without a NextAuth session, otherwise the
// proxy 401s guests before the BFF can call the backend LLM.
const PUBLIC_API_PATHS = ["/api/chat", "/api/documents", "/api/memory"]
/** Cookie set by /api/chat on a guest's first message — lets returning guests
 *  bypass the login gate without a NextAuth session token. */
const GUEST_ID_COOKIE = "aura-guest-id"
const PUBLIC_FILE =
  /\.(?:svg|png|jpg|jpeg|gif|webp|ico|json|webmanifest|js|css|map|txt|woff2?)$/i

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Allow public paths and static assets from /public through
  if (
    PUBLIC_FILE.test(pathname) ||
    PUBLIC_PATHS.some((p) => pathname.startsWith(p)) ||
    PUBLIC_API_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))
  ) {
    return NextResponse.next()
  }

  // Returning guests (have the guest-id cookie but no NextAuth token) should
  // pass straight through to the chat rather than being sent to /login.
  if (req.cookies.has(GUEST_ID_COOKIE)) {
    return NextResponse.next()
  }

  let secret: string
  try {
    secret = getNextAuthSecret()
  } catch (err) {
    console.error("[proxy] auth secret misconfigured:", err)
    return NextResponse.json(
      { error: "Authentication is temporarily unavailable", code: "INTERNAL" },
      { status: 500 },
    )
  }

  // Check for a valid NextAuth session token
  const token = await getToken({
    req,
    secret,
  })

  if (!token) {
    if (pathname.startsWith("/api/")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }
    const loginUrl = new URL("/login", req.url)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
