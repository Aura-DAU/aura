import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { getToken } from "next-auth/jwt"

import { getNextAuthSecret } from "@/lib/auth/secrets"

/** Paths that never need an auth check at all (assets, NextAuth internals, etc.) */
const ALWAYS_PUBLIC_PATHS = ["/api/auth", "/_next", "/favicon.ico", "/offline"]
// Anonymous guest chat (#206): /api/chat mints its own guest JWT + cookie
// quota key. Must stay reachable without a NextAuth session, otherwise the
// proxy 401s guests before the BFF can call the backend LLM.
const PUBLIC_API_PATHS = ["/api/chat", "/api/documents", "/api/memory"]
const PUBLIC_FILE =
  /\.(?:svg|png|jpg|jpeg|gif|webp|ico|json|webmanifest|js|css|map|txt|woff2?)$/i

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Static assets and NextAuth internals — never need a session check.
  if (
    PUBLIC_FILE.test(pathname) ||
    ALWAYS_PUBLIC_PATHS.some((p) => pathname.startsWith(p)) ||
    PUBLIC_API_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`))
  ) {
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

  const token = await getToken({ req, secret })

  // Already signed in → skip the login page and go straight to the app.
  if (token && pathname === "/login") {
    return NextResponse.redirect(new URL("/", req.url))
  }

  // Not signed in → gate all non-login pages.
  if (!token) {
    if (pathname === "/login") {
      // Let unauthenticated users see the login page.
      return NextResponse.next()
    }
    if (pathname.startsWith("/api/")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
    }
    return NextResponse.redirect(new URL("/login", req.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
}
