import { SignJWT, jwtVerify } from "jose"

const JWT_SECRET = process.env.INTERNAL_JWT_SECRET || "fallback-secret-for-development-only"
const secretKey = new TextEncoder().encode(JWT_SECRET)

export interface InternalJwtPayload {
  role: "student" | "faculty" | "admin"
  erpId: string
  department?: string
  [key: string]: unknown
}

/**
 * Signs a short-lived internal JWT for communicating with the Python backend.
 */
export async function signInternalJwt(payload: InternalJwtPayload): Promise<string> {
  return new SignJWT({ ...payload })
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("1h") // Short-lived
    .sign(secretKey)
}

/**
 * Verifies an internal JWT.
 */
export async function verifyInternalJwt(token: string): Promise<InternalJwtPayload> {
  const { payload } = await jwtVerify(token, secretKey)
  return payload as unknown as InternalJwtPayload
}
