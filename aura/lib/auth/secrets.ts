/**
 * Shared secret readers for NextAuth and middleware.
 * Production must fail closed — never fall back to mock secrets.
 */

function isProductionRuntime(): boolean {
  return process.env.NODE_ENV === "production" && !process.env.NEXT_PHASE
}

export function getNextAuthSecret(): string {
  const secret = process.env.NEXTAUTH_SECRET
  if (secret) return secret
  if (isProductionRuntime()) {
    throw new Error(
      "FATAL: NEXTAUTH_SECRET is not set. Set it before starting the server.",
    )
  }
  return "mock-nextauth-secret"
}

export type GoogleOAuthCredentials = {
  clientId: string
  clientSecret: string
}

/**
 * Returns Google OAuth creds when both env vars are set; otherwise null.
 * Guest chat and /api/auth/session must keep working without Google —
 * only the Google sign-in provider is omitted when these are missing.
 */
export function getGoogleOAuthCredentials(): GoogleOAuthCredentials | null {
  const clientId = process.env.GOOGLE_CLIENT_ID?.trim()
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET?.trim()
  if (clientId && clientSecret) {
    return { clientId, clientSecret }
  }
  return null
}

/** Prefer getGoogleOAuthCredentials — Google is optional for guest chat. */
export function requireGoogleOAuthCredentials(): GoogleOAuthCredentials {
  const creds = getGoogleOAuthCredentials()
  if (creds) return creds
  if (isProductionRuntime()) {
    console.warn(
      "[auth] GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET unset — Google sign-in disabled.",
    )
    return {
      clientId: "missing-google-client-id",
      clientSecret: "missing-google-client-secret",
    }
  }
  return {
    clientId: "mock-client-id",
    clientSecret: "mock-client-secret",
  }
}

export function requireInternalResolveSecret(): string {
  const secret = process.env.INTERNAL_RESOLVE_SECRET
  if (secret) return secret
  if (isProductionRuntime()) {
    throw new Error(
      "FATAL: INTERNAL_RESOLVE_SECRET is not set. Set it before starting the server.",
    )
  }
  return ""
}
