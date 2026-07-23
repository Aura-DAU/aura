import jwt from "jsonwebtoken"

const JWT_SECRET = process.env.INTERNAL_JWT_SECRET || "test-internal-secret-for-auth-middleware"

export interface InternalJwtPayload {
  role: "student" | "faculty" | "admin" | "guest"
  erpId: string
  department?: string
  currentYear?: number
  currentSem?: number
  currentSec?: string
  facultyInitials?: string
  fullName?: string
  [key: string]: unknown
}

/**
 * Signs a short-lived internal JWT for communicating with the Python backend.
 * Expiry is set to 15m to ensure security.
 */
export function signInternalJwt(payload: InternalJwtPayload): string {
  if (!JWT_SECRET) {
    throw new Error("FATAL: INTERNAL_JWT_SECRET is not set. Set it before starting the server.")
  }
  return jwt.sign(
    {
      role: payload.role,
      erpId: payload.erpId,
      department: payload.department,
      currentYear: payload.currentYear,
      currentSem: payload.currentSem,
      currentSec: payload.currentSec,
      facultyInitials: payload.facultyInitials,
      fullName: payload.fullName,
    },
    JWT_SECRET,
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
  if (!JWT_SECRET) {
    throw new Error("FATAL: INTERNAL_JWT_SECRET is not set. Set it before starting the server.")
  }
  return jwt.verify(token, JWT_SECRET) as InternalJwtPayload
}
