import jwt from "jsonwebtoken"

function isProductionRuntime(): boolean {
  return process.env.NODE_ENV === "production" && !process.env.NEXT_PHASE
}

function getJwtSecret(): string {
  const secret = process.env.INTERNAL_JWT_SECRET
  if (secret) return secret
  if (isProductionRuntime()) {
    throw new Error(
      "FATAL: INTERNAL_JWT_SECRET is not set. Set it before starting the server.",
    )
  }
  return "test-internal-secret-for-auth-middleware"
}

export interface InternalJwtPayload {
  role: "student" | "faculty" | "admin" | "guest"
  erpId: string
  department?: string
  email?: string
  // Timetable-cohort fields — display/lookup only, read by the FastAPI
  // backend's Identity dataclass (see server/api/auth.py) purely to resolve
  // which timetable cohort belongs to this student. Never used for authz.
  fullName?: string
  currentYear?: number
  currentSem?: number
  currentSec?: string
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
      fullName: payload.fullName,
      currentYear: payload.currentYear,
      currentSem: payload.currentSem,
      currentSec: payload.currentSec,
    },
    getJwtSecret(),
    {
      algorithm: "HS256",
      expiresIn: "15m",
    },
  )
}

/**
 * Verifies an internal JWT.
 */
export function verifyInternalJwt(token: string): InternalJwtPayload {
  return jwt.verify(token, getJwtSecret()) as InternalJwtPayload
}
