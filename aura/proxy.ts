import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"
import { getToken } from "next-auth/jwt"

import { getNextAuthSecret } from "@/lib/auth/secrets"

const PUBLIC_PATHS = ["/login", "/api/auth", "/_next", "/favicon.ico", "/offline"]
const EXACT_PUBLIC_PATHS = ["/"]
const PUBLIC_FILE =
  /\.(?:svg|png|jpg|jpeg|gif|webp|ico|json|webmanifest|js|css|map|txt|woff2?)$/i

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl

  // Allow public paths and static assets from /public through
  if (
    PUBLIC_FILE.test(pathname) ||
    PUBLIC_PATHS.some((p) => pathname.startsWith(p)) ||
    EXACT_PUBLIC_PATHS.includes(pathname)
  ) {
    return NextResponse.next()
  }

  const secret = getNextAuthSecret()

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
