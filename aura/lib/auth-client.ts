import { signOut } from "next-auth/react"
import { toastError } from "@/lib/toast"

/**
 * Sign out and clear client session state.
 */
export async function logout(): Promise<void> {
  await signOut({ callbackUrl: "/login" })
}

/**
 * Same-origin fetch wrapper for Next.js BFF routes.
 *
 * Auth is the NextAuth session cookie (httpOnly) — never an INTERNAL JWT in
 * browser JS. BFF handlers mint short-lived server-side JWTs for FastAPI.
 * credentials: "same-origin" ensures the session cookie is always sent.
 */
export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  const response = await fetch(input, {
    ...init,
    credentials: "same-origin",
  })

  if (response.status === 401) {
    console.error("[auth-client] 401 Unauthorized — session missing or expired")
    toastError("Your session expired. Please sign in again.")
    await logout()
  }

  return response
}

/**
 * True when a NextAuth session cookie is present (via /api/auth/session).
 * Used by dashboards that need to wait for auth before firing BFF calls —
 * does not expose any backend JWT to the browser.
 */
export async function ensureSession(): Promise<boolean> {
  try {
    const res = await fetch("/api/auth/session", { credentials: "same-origin" })
    if (!res.ok) return false
    const data = (await res.json()) as { user?: { erpId?: string } } | null
    return Boolean(data?.user?.erpId)
  } catch (err) {
    console.error("[auth-client] Failed to check session:", err)
    return false
  }
}
