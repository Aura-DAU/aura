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

export function requireGoogleOAuthCredentials(): {
  clientId: string
  clientSecret: string
} {
  const clientId = process.env.GOOGLE_CLIENT_ID
  const clientSecret = process.env.GOOGLE_CLIENT_SECRET
  if (clientId && clientSecret) {
    return { clientId, clientSecret }
  }
  if (isProductionRuntime()) {
    throw new Error(
      "FATAL: GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in production.",
    )
  }
  return {
    clientId: clientId || "mock-client-id",
    clientSecret: clientSecret || "mock-client-secret",
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
