import { signOut } from "next-auth/react"
import { toastError } from "@/lib/toast"

let inMemoryToken: string | null = null

export function setToken(token: string | null) {
  inMemoryToken = token
}

export function getToken(): string | null {
  return inMemoryToken
}

/**
 * Hydrates the in-memory access token by fetching the active session.
 */
export async function initAuth(): Promise<string | null> {
  try {
    const res = await fetch("/api/auth/token")
    if (res.ok) {
      const { token } = await res.json()
      setToken(token || null)
      return token || null
    }
  } catch (err) {
    console.error("[auth-client] Failed to fetch token:", err)
  }
  setToken(null)
  return null
}

/**
 * Sign out and clear in-memory tokens.
 */
export async function logout(): Promise<void> {
  setToken(null)
  await signOut({ callbackUrl: "/login" })
}

/**
 * Fetch wrapper that appends the client's internal JWT access token,
 * handles silent 401 refreshes, and triggers logout if unauthorized.
 */
export async function apiFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  let token = getToken()

  // Ensure a token exists before authenticated calls (avoids dashboard race on mount).
  if (!token) {
    token = await initAuth()
  }

  const headers = new Headers(init?.headers)
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  let response = await fetch(input, { ...init, headers })

  if (response.status === 401) {
    console.warn("[auth-client] 401 Unauthorized, attempting silent session refresh...")
    token = await initAuth()
    if (token) {
      headers.set("Authorization", `Bearer ${token}`)
      response = await fetch(input, { ...init, headers })
    } else {
      console.error("[auth-client] Silent refresh failed, logging out...")
      toastError("Your session expired. Please sign in again.")
      await logout()
    }
  }

  return response
}
