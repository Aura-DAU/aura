import { NextResponse } from "next/server"

/**
 * Removed: this endpoint previously returned a live INTERNAL JWT to browser JS.
 * XSS (or any script) could then call /backend/* directly with that Bearer token.
 * BFF routes mint JWTs server-side after getServerSession(); clients must not
 * hold them. Prefer /api/auth/session for "am I signed in?" checks.
 */
export async function GET() {
  return NextResponse.json(
    {
      error:
        "Internal tokens are no longer issued to the browser. Use the session cookie and /api/* BFF routes.",
    },
    { status: 410 },
  )
}
