import { NextResponse } from "next/server"
import { cookies } from "next/headers"
import { encode } from "next-auth/jwt"
import {
  readOrMintGuestCookies,
  guestErpId,
  guestCookieOptions,
  GUEST_ID_COOKIE,
  GUEST_SECRET_COOKIE,
} from "@/lib/auth/guest-identity"
import { getNextAuthSecret } from "@/lib/auth/secrets"

const SESSION_MAX_AGE = 8 * 60 * 60 // 8 h — matches authOptions

/**
 * GET /api/auth/guest
 *
 * Mints the guest identity cookies and creates a real NextAuth JWT session
 * for the guest. This lets the proxy's getToken() call recognise guests
 * without needing a separate cookie-bypass in proxy.ts.
 *
 * Flow: /login → (click "Continue as Guest") → /api/auth/guest → /
 */
export async function GET(request: Request) {
  const cookieStore = await cookies()
  const guestCookies = readOrMintGuestCookies(cookieStore)
  const erpId = guestErpId(guestCookies)

  // Build the NextAuth JWT payload for this guest.
  const now = Math.floor(Date.now() / 1000)
  const jwtToken = await encode({
    token: {
      sub: guestCookies.guestId,
      role: "guest",
      erpId,
      iat: now,
      exp: now + SESSION_MAX_AGE,
      jti: crypto.randomUUID(),
    },
    secret: getNextAuthSecret(),
    maxAge: SESSION_MAX_AGE,
  })

  const isProduction = process.env.NODE_ENV === "production"
  const sessionCookieName = isProduction
    ? "__Secure-next-auth.session-token"
    : "next-auth.session-token"

  const response = NextResponse.redirect(new URL("/", request.url))

  // Set the guest identity cookies (used by /api/chat for quota keying).
  const guestOpts = guestCookieOptions()
  response.cookies.set(GUEST_ID_COOKIE, guestCookies.guestId, guestOpts)
  response.cookies.set(GUEST_SECRET_COOKIE, guestCookies.guestSecret, guestOpts)

  // Set the NextAuth session cookie so the proxy gate passes on subsequent requests.
  response.cookies.set(sessionCookieName, jwtToken, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE,
    secure: isProduction,
  })

  return response
}
