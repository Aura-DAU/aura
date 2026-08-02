import { randomUUID, createHmac } from "crypto"

/**
 * SEC-07 fix: previously, `aura-guest-id` alone (a random UUID, httpOnly)
 * was used directly as the `erpId` claim in the internal JWT — i.e. as the
 * quota-bucket key for the 10/day guest limit. httpOnly stops JS-based
 * theft, but the review's threat model is broader: "any user who can
 * observe one guest's aura-guest-id cookie value can include it in their
 * own request to share that guest's quota bucket" (e.g. via a log line, a
 * proxy/debugging tool, or a shared/compromised machine).
 *
 * The fix binds the effective guest id to TWO independent per-browser
 * cookie values (`aura-guest-id` + `aura-guest-secret`) via HMAC, using
 * INTERNAL_JWT_SECRET as the key. An attacker who observes only one of the
 * two values (e.g. a log line that happens to record one cookie but not
 * the other) can no longer reproduce the resulting quota-bucket key.
 */

const GUEST_ID_COOKIE = "aura-guest-id"
const GUEST_SECRET_COOKIE = "aura-guest-secret"
const GUEST_COOKIE_MAX_AGE = 60 * 60 * 24 * 365 // 1 year

function isProductionRuntime(): boolean {
  return process.env.NODE_ENV === "production" && !process.env.NEXT_PHASE
}

function getBindingSecret(): string {
  const secret = process.env.INTERNAL_JWT_SECRET
  if (secret) return secret
  if (isProductionRuntime()) {
    throw new Error("FATAL: INTERNAL_JWT_SECRET is not set. Set it before starting the server.")
  }
  return "test-internal-secret-for-auth-middleware"
}

function deriveErpId(guestId: string, guestSecret: string): string {
  const digest = createHmac("sha256", getBindingSecret())
    .update(`${guestId}:${guestSecret}`)
    .digest("hex")
    .slice(0, 32)
  return `GUEST-${digest}`
}

export interface GuestCookieValues {
  guestId: string
  guestSecret: string
  isNew: boolean
}

/** Reads the guest cookie pair, minting either/both that are missing/invalid. */
export function readOrMintGuestCookies(cookieStore: {
  get(name: string): { value: string } | undefined
}): GuestCookieValues {
  const existingId = cookieStore.get(GUEST_ID_COOKIE)?.value
  const existingSecret = cookieStore.get(GUEST_SECRET_COOKIE)?.value

  const guestId = existingId && existingId.length <= 64 ? existingId : `GUEST-${randomUUID()}`
  const guestSecret = existingSecret && existingSecret.length <= 64 ? existingSecret : randomUUID()

  const isNew = guestId !== existingId || guestSecret !== existingSecret
  return { guestId, guestSecret, isNew }
}

/** The value to actually use as `erpId` for quota keying / the internal JWT. */
export function guestErpId(values: GuestCookieValues): string {
  return deriveErpId(values.guestId, values.guestSecret)
}

/** Cookie options shared by both guest cookies. */
export function guestCookieOptions() {
  return {
    httpOnly: true as const,
    sameSite: "lax" as const,
    secure: process.env.NODE_ENV === "production",
    path: "/",
    maxAge: GUEST_COOKIE_MAX_AGE,
  }
}

export { GUEST_ID_COOKIE, GUEST_SECRET_COOKIE }
