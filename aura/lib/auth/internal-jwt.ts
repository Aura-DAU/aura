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

/** Must match server/api/auth.py INTERNAL_JWT_ISSUER / AUDIENCE. */
export const INTERNAL_JWT_ISSUER = "aura-next"
export const INTERNAL_JWT_AUDIENCE = "aura-api"

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
 * Expiry is 15m. iss/aud bind the token to the Next→API hop so calendar OAuth
 * state JWTs (different aud) cannot be confused with session tokens.
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
      issuer: INTERNAL_JWT_ISSUER,
      audience: INTERNAL_JWT_AUDIENCE,
    },
  )
}

/**
 * Verifies an internal JWT (iss/aud/exp/alg).
 */
export function verifyInternalJwt(token: string): InternalJwtPayload {
  return jwt.verify(token, getJwtSecret(), {
    algorithms: ["HS256"],
    issuer: INTERNAL_JWT_ISSUER,
    audience: INTERNAL_JWT_AUDIENCE,
  }) as InternalJwtPayload
}
