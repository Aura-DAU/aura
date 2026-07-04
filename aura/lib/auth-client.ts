import { signOut } from "next-auth/react"

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
    const res = await fetch("/api/auth/session")
    if (res.ok) {
      const session = await res.json()
      const token = session?.accessToken || null
      setToken(token)
      return token
    }
  } catch (err) {
    console.error("[auth-client] Failed to fetch session:", err)
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
  
  const headers = new Headers(init?.headers)
  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  let response = await fetch(input, { ...init, headers })

  if (response.status === 401) {
    console.warn("[auth-client] 401 Unauthorized, attempting silent session refresh...")
    // Perform silent refresh
    token = await initAuth()
    if (token) {
      // Retry original request with the fresh token
      headers.set("Authorization", `Bearer ${token}`)
      response = await fetch(input, { ...init, headers })
    } else {
      console.error("[auth-client] Silent refresh failed, logging out...")
      await logout()
    }
  }

  return response
}
