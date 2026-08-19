import { NextAuthOptions, DefaultSession } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import { backendUrl } from "@/lib/api/backend"
import {
  getGoogleOAuthCredentials,
  getNextAuthSecret,
  requireInternalResolveSecret,
} from "@/lib/auth/secrets"

type Role = "student" | "faculty" | "admin" | "guest"

declare module "next-auth" {
  interface Session {
    user: {
      role: Role
      erpId: string
      department?: string
      // Timetable-cohort fields, populated from user_identity_map at login.
      // Display/lookup only — never used for authorization decisions.
      fullName?: string
      currentYear?: number
      currentSem?: number
      currentSec?: string
      currentLabGroup?: string
      facultyInitials?: string
    } & DefaultSession["user"]
  }

  interface User {
    role?: Role
    erpId?: string
    department?: string
    fullName?: string
    currentYear?: number
    currentSem?: number
    currentSec?: string
    currentLabGroup?: string
    facultyInitials?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: Role
    erpId?: string
    department?: string
    fullName?: string
    currentYear?: number
    currentSem?: number
    currentSec?: string
    currentLabGroup?: string
    facultyInitials?: string
  }
}

interface ErpIdentity {
  role: Role
  erpId: string
  department: string
  fullName?: string
  currentYear?: number
  currentSem?: number
  currentSec?: string
  currentLabGroup?: string
  facultyInitials?: string
}

/**
 * Fetches the user's ERP Identity from the backend Auth DB. This is the
 * ONLY place student_profile fields (name/role/current_year/current_sem/
 * current_sec) enter AURA — pulled once from user_identity_map at login
 * time via /internal/resolve-identity, then carried in the session + signed
 * internal JWT for the rest of the session.
 */
async function lookupErpIdentity(email: string): Promise<ErpIdentity | null> {
  try {
    const res = await fetch(backendUrl(`/internal/resolve-identity?email=${encodeURIComponent(email)}`), {
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Secret": requireInternalResolveSecret(),
      }
    })

    if (!res.ok) {
      console.error("[NextAuth] Failed to lookup ERP identity:", res.status, await res.text().catch(() => ""))
      return null
    }

    const data = await res.json()
    return {
      role: data.role,
      erpId: data.erp_id || data.erpId,
      department: data.department || data.dept || "",
      fullName: data.full_name || data.fullName || undefined,
      currentYear: data.current_year ?? data.currentYear ?? undefined,
      currentSem: data.current_sem ?? data.currentSem ?? undefined,
      currentSec: data.current_sec ?? data.currentSec ?? undefined,
      currentLabGroup: data.current_lab_group ?? data.currentLabGroup ?? undefined,
      facultyInitials: data.faculty_initials ?? data.facultyInitials ?? undefined,
    }
  } catch (error) {
    console.error("[NextAuth] Error calling lookup endpoint:", error)
    return null
  }
}

export const authOptions: NextAuthOptions = {
  // A getter, not a plain array: NextAuth (and every getServerSession(authOptions)
  // call across the app) reads `.providers` fresh on each access instead of once
  // at module import. Previously `googleCreds` was resolved to a top-level const
  // and baked into a static providers array at cold-start/import time — on a
  // serverless or edge deployment that import can happen before secrets are
  // injected, or the module can simply stay warm for a long time, so a
  // credential fix/rotation wouldn't take effect until the process restarted.
  get providers() {
    const googleCreds = getGoogleOAuthCredentials()
    if (!googleCreds && process.env.NODE_ENV === "production") {
      console.warn(
        "[auth] GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET unset — Google Workspace sign-in disabled; guest chat still works.",
      )
    }
    return [
      ...(googleCreds
        ? [
          GoogleProvider({
            clientId: googleCreds.clientId,
            clientSecret: googleCreds.clientSecret,
            authorization: {
              params: {
                prompt: "select_account",
              },
            },
          }),
        ]
        : []),
      // SEC-02 fix: previously gated only on `NODE_ENV === "development"`
      // with hardcoded passwords (Student@123, Faculty@123, Admin@123)
      // baked into the source. If NODE_ENV were ever left unset/misconfigured
      // in staging (a common operator mistake), those hardcoded passwords
      // would grant real login — including admin — in a deployed instance.
      // Now: (1) demo accounts require an explicit opt-in flag, (2) that
      // flag is hard-blocked in production no matter what, and (3) the
      // passwords themselves must come from the environment — there is no
      // in-source fallback to leak.
      ...(process.env.ENABLE_DEMO_ACCOUNTS === "true" && process.env.NODE_ENV !== "production"
        ? [
          CredentialsProvider({
            name: "Demo Account",
            credentials: {
              email: { label: "Email", type: "text" },
              password: { label: "Password", type: "password" },
            },
            async authorize(credentials) {
              const studentPw = process.env.DEMO_STUDENT_PASSWORD
              const facultyPw = process.env.DEMO_FACULTY_PASSWORD
              const adminPw = process.env.DEMO_ADMIN_PASSWORD

              if (
                studentPw &&
                credentials?.email === "demo.student@dau.ac.in" &&
                credentials?.password === studentPw
              ) {
                return { id: "demo-stud", email: credentials.email, name: "Demo Student" }
              }
              if (
                facultyPw &&
                credentials?.email === "demo.faculty@daiict.ac.in" &&
                credentials?.password === facultyPw
              ) {
                return { id: "demo-fac", email: credentials.email, name: "Demo Faculty" }
              }
              if (
                adminPw &&
                credentials?.email === "demo.admin@dau.ac.in" &&
                credentials?.password === adminPw
              ) {
                return { id: "demo-admin", email: credentials.email, name: "Demo Admin" }
              }
              return null
            },
          }),
        ]
        : []),
    ]
  },
  session: {
    strategy: "jwt",
    // 30-day persistent login. The sliding updateAge means the JWT is only
    // re-signed when it's older than 24 h — reducing unnecessary re-fetches
    // while keeping the 30-day window alive for active users.
    maxAge: 30 * 24 * 60 * 60, // 30 days
    updateAge: 24 * 60 * 60, // refresh JWT at most once per day
  },
  // Force Secure cookies in production (NextAuth also sets httpOnly + SameSite=lax).
  useSecureCookies: process.env.NODE_ENV === "production",
  cookies: {
    sessionToken: {
      name:
        process.env.NODE_ENV === "production"
          ? "__Secure-next-auth.session-token"
          : "next-auth.session-token",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: process.env.NODE_ENV === "production",
        // Explicit maxAge makes this a persistent cookie (not a session cookie).
        // Without this the browser discards it on close even if maxAge is set
        // in the NextAuth session config above.
        maxAge: 30 * 24 * 60 * 60, // 30 days in seconds
      },
    },
  },
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        const email = user.email || ""
        // Only official @dau.ac.in accounts may sign in. Anyone else
        // (including personal Gmail addresses) should use the anonymous
        // guest chat instead — see the "Continue as Guest" option on
        // /login and the anonymous cookie flow in app/api/chat/route.ts.
        if (!email.endsWith("@dau.ac.in")) {
          return "/login?error=DomainNotAllowed"
        }

        try {
          const res = await fetch(backendUrl(`/internal/resolve-identity?email=${encodeURIComponent(email)}`), {
            headers: {
              "Content-Type": "application/json",
              "X-Internal-Secret": requireInternalResolveSecret(),
            }
          })

          if (res.status === 404) {
            return "/login?error=NotRegistered"
          }
          if (!res.ok) {
            return "/login?error=ServerError"
          }

          const data = await res.json()
          user.role = data.role
          user.erpId = data.erp_id || data.erpId
          user.department = data.department || data.dept || ""
          user.fullName = data.full_name || data.fullName || undefined
          user.currentYear = data.current_year ?? data.currentYear ?? undefined
          user.currentSem = data.current_sem ?? data.currentSem ?? undefined
          user.currentSec = data.current_sec ?? data.currentSec ?? undefined
          user.currentLabGroup = data.current_lab_group ?? data.currentLabGroup ?? undefined
          user.facultyInitials = data.faculty_initials ?? data.facultyInitials ?? undefined
          return true
        } catch (err) {
          console.error("[NextAuth] SignIn callback lookup failed:", err)
          return "/login?error=ServerError"
        }
      }
      return true
    },
    async jwt({ token, user }) {
      // If it's the first sign-in (user object is available), lookup the ERP identity
      const demoAccountsEnabled =
        process.env.ENABLE_DEMO_ACCOUNTS === "true" && process.env.NODE_ENV !== "production"
      if (user && user.email) {
        if (demoAccountsEnabled && user.email === "demo.student@dau.ac.in") {
          token.role = "student"
          token.erpId = "DEMO123"
          token.department = "ICT"
          token.fullName = "Demo Student"
          token.currentYear = 3
          token.currentSem = 5
          token.currentSec = "A"
        } else if (demoAccountsEnabled && user.email === "demo.faculty@daiict.ac.in") {
          token.role = "faculty"
          token.erpId = "FAC123"
          token.department = "ICT"
          token.fullName = "Demo Faculty"
        } else if (demoAccountsEnabled && user.email === "demo.admin@dau.ac.in") {
          token.role = "admin"
          token.erpId = "ADM123"
          token.department = "IT"
          token.fullName = "Demo Admin"
        } else if (user.erpId) {
          token.role = user.role
          token.erpId = user.erpId
          token.department = user.department
          token.fullName = user.fullName
          token.currentYear = user.currentYear
          token.currentSem = user.currentSem
          token.currentSec = user.currentSec
          token.currentLabGroup = user.currentLabGroup
        } else {
          const erpData = await lookupErpIdentity(user.email)
          if (erpData) {
            token.role = erpData.role
            token.erpId = erpData.erpId
            token.department = erpData.department
            token.fullName = erpData.fullName
            token.currentYear = erpData.currentYear
            token.currentSem = erpData.currentSem
            token.currentSec = erpData.currentSec
            token.currentLabGroup = erpData.currentLabGroup
          }
        }
      }

      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.role = token.role as Role
        session.user.erpId = token.erpId as string
        session.user.department = token.department as string | undefined
        session.user.fullName = token.fullName as string | undefined
        session.user.currentYear = token.currentYear as number | undefined
        session.user.currentSem = token.currentSem as number | undefined
        session.user.currentSec = token.currentSec as string | undefined
        session.user.currentLabGroup = token.currentLabGroup as string | undefined
      }
      return session
    },
  },
  secret: getNextAuthSecret(),
  pages: {
    signIn: "/login",
    error: "/login",
  },
}