import { NextResponse } from "next/server"
import { cookies } from "next/headers"
import {
  readOrMintGuestCookies,
  guestCookieOptions,
  GUEST_ID_COOKIE,
  GUEST_SECRET_COOKIE,
} from "@/lib/auth/guest-identity"

/**
 * GET /api/auth/guest
 *
 * Mints (or refreshes) the two guest-identity cookies and redirects the user
 * to the chat root. Called by the "Continue as Guest" button on /login so
 * that the proxy sees the guest cookie before gating access to "/".
 */
export async function GET(request: Request) {
  const cookieStore = await cookies()
  const guestCookies = readOrMintGuestCookies(cookieStore)

  const opts = guestCookieOptions()

  const response = NextResponse.redirect(new URL("/", request.url))

  if (guestCookies.isNew) {
    response.cookies.set(GUEST_ID_COOKIE, guestCookies.guestId, opts)
    response.cookies.set(GUEST_SECRET_COOKIE, guestCookies.guestSecret, opts)
  }

  return response
}
