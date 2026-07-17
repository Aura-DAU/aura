import jwt from "jsonwebtoken"

function getJwtSecret(): string {
  const secret = process.env.INTERNAL_JWT_SECRET
  if (!secret) {
    if (process.env.NODE_ENV === "production" && !process.env.NEXT_PHASE) {
      throw new Error("FATAL: INTERNAL_JWT_SECRET is not set. Set it before starting the server.")
    }
    return "test-internal-secret-for-auth-middleware"
  }
  return secret
}

export interface InternalJwtPayload {
  role: "student" | "faculty" | "admin" | "guest"
  erpId: string
  department?: string
  email?: string
  [key: string]: unknown
}

/**
 * Signs a short-lived internal JWT for communicating with the Python backend.
 * Expiry is set to 15m to ensure security.
 */
export function signInternalJwt(payload: InternalJwtPayload): string {
  return jwt.sign(
    {
      role: payload.role,
      erpId: payload.erpId,
      department: payload.department,
      email: payload.email,
    },
    getJwtSecret(),
    {
      algorithm: "HS256",
      expiresIn: "15m",
    }
  )
}

/**
 * Verifies an internal JWT.
 */
export function verifyInternalJwt(token: string): InternalJwtPayload {
  return jwt.verify(token, getJwtSecret()) as InternalJwtPayload
}
