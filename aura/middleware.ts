import { NextResponse } from "next/server"
import type { NextRequest } from "next/server"

/**
 * Routes that are always public — no session or guest cookie needed.
 * The matcher below already excludes /_next/*, /api/auth/*, and static
 * files so this list only needs to cover app-level public paths.
 */
const PUBLIC_PATHS = new Set(["/login", "/offline"])

/**
 * Cookie names used by NextAuth JWT strategy (dev vs. production).
 * We just need to detect the presence of either one; we don't validate
 * the JWT here (that's NextAuth's job on the API route).
 */
const SESSION_COOKIE_NAMES = [
  "next-auth.session-token",            // development
  "__Secure-next-auth.session-token",   // production (Secure flag)
]

/** Guest identity cookie — set by /api/chat when a guest sends their first message. */
const GUEST_ID_COOKIE = "aura-guest-id"

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Always allow public app paths.
  if (PUBLIC_PATHS.has(pathname)) {
    return NextResponse.next()
  }

  // Allow if user has a valid NextAuth session cookie.
  const hasSession = SESSION_COOKIE_NAMES.some(
    (name) => request.cookies.has(name),
  )
  if (hasSession) return NextResponse.next()

  // Allow if user has already visited as a guest (guest-id cookie present).
  if (request.cookies.has(GUEST_ID_COOKIE)) return NextResponse.next()

  // No session, no guest cookie → send to login.
  const loginUrl = request.nextUrl.clone()
  loginUrl.pathname = "/login"
  return NextResponse.redirect(loginUrl)
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     *   - /api/auth/* (NextAuth endpoints must be public)
     *   - /_next/* (Next.js internals)
     *   - /static/* (static files)
     *   - Common static file extensions
     */
    "/((?!api/auth|_next|static|.*\\.(?:png|jpg|jpeg|gif|webp|svg|ico|css|js|woff2?|ttf|eot|map)).*)",
  ],
}
