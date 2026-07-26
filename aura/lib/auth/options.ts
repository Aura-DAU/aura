import { NextAuthOptions, DefaultSession } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import { backendUrl } from "@/lib/api/backend"
import {
  getNextAuthSecret,
  requireGoogleOAuthCredentials,
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
    }
  } catch (error) {
    console.error("[NextAuth] Error calling lookup endpoint:", error)
    return null
  }
}

const googleCreds = requireGoogleOAuthCredentials()

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: googleCreds.clientId,
      clientSecret: googleCreds.clientSecret,
      authorization: {
        params: {
          prompt: "select_account",
        },
      },
    }),
    ...(process.env.NODE_ENV === "development" ? [
      CredentialsProvider({
        name: "Demo Account",
        credentials: {
          email: { label: "Email", type: "text" },
          password: { label: "Password", type: "password" }
        },
        async authorize(credentials) {
          if (credentials?.email === "demo.student@dau.ac.in" && credentials?.password === "Student@123") {
            return { id: "demo-stud", email: credentials.email, name: "Demo Student" }
          }
          if (credentials?.email === "demo.faculty@daiict.ac.in" && credentials?.password === "Faculty@123") {
            return { id: "demo-fac", email: credentials.email, name: "Demo Faculty" }
          }
          if (credentials?.email === "demo.admin@dau.ac.in" && credentials?.password === "Admin@123") {
            return { id: "demo-admin", email: credentials.email, name: "Demo Admin" }
          }
          return null
        }
      })
    ] : [])
  ],
  session: {
    strategy: "jwt",
    // Bound session lifetime so stolen cookies expire without waiting for
    // Google account recovery. Sliding refresh still renews while active.
    maxAge: 8 * 60 * 60, // 8 hours
    updateAge: 60 * 60, // refresh JWT at most once per hour
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
      if (user && user.email) {
        if (process.env.NODE_ENV === "development" && user.email === "demo.student@dau.ac.in") {
          token.role = "student"
          token.erpId = "DEMO123"
          token.department = "ICT"
          token.fullName = "Demo Student"
          token.currentYear = 3
          token.currentSem = 5
          token.currentSec = "A"
        } else if (process.env.NODE_ENV === "development" && user.email === "demo.faculty@daiict.ac.in") {
          token.role = "faculty"
          token.erpId = "FAC123"
          token.department = "ICT"
          token.fullName = "Demo Faculty"
        } else if (process.env.NODE_ENV === "development" && user.email === "demo.admin@dau.ac.in") {
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
