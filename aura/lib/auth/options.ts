import { NextAuthOptions, DefaultSession } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import { backendUrl } from "@/lib/api/backend"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    user: {
      role: "student" | "faculty" | "admin" | "guest"
      erpId: string
      department?: string
      currentYear?: number
      currentSem?: number
      currentSec?: string
      facultyInitials?: string
      fullName?: string
    } & DefaultSession["user"]
  }

  interface User {
    role?: "student" | "faculty" | "admin" | "guest"
    erpId?: string
    department?: string
    currentYear?: number
    currentSem?: number
    currentSec?: string
    facultyInitials?: string
    fullName?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: "student" | "faculty" | "admin" | "guest"
    erpId?: string
    department?: string
    currentYear?: number
    currentSem?: number
    currentSec?: string
    facultyInitials?: string
    fullName?: string
    accessToken?: string
  }
}

/**
 * Fetches the user's ERP Identity from the backend Auth DB.
 */
async function lookupErpIdentity(email: string): Promise<{
  role: "student" | "faculty" | "admin" | "guest"
  erpId: string
  department: string
  currentYear?: number
  currentSem?: number
  currentSec?: string
  facultyInitials?: string
  fullName?: string
} | null> {
  try {
    const res = await fetch(backendUrl(`/internal/resolve-identity?email=${encodeURIComponent(email)}`), {
      headers: {
        "Content-Type": "application/json",
        "X-Internal-Secret": process.env.INTERNAL_RESOLVE_SECRET || ""
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
      currentYear: data.current_year ?? undefined,
      currentSem: data.current_sem ?? undefined,
      currentSec: data.current_sec ?? undefined,
      facultyInitials: data.faculty_initials ?? undefined,
      fullName: data.full_name ?? undefined,
    }
  } catch (error) {
    console.error("[NextAuth] Error calling lookup endpoint:", error)
    return null
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: (() => {
        const id = process.env.GOOGLE_CLIENT_ID
        if (!id && process.env.NODE_ENV === "production" && !process.env.NEXT_PHASE) {
          console.warn("WARNING: GOOGLE_CLIENT_ID is not set.")
        }
        return id || "mock-client-id"
      })(),
      clientSecret: (() => {
        const secret = process.env.GOOGLE_CLIENT_SECRET
        if (!secret && process.env.NODE_ENV === "production" && !process.env.NEXT_PHASE) {
          console.warn("WARNING: GOOGLE_CLIENT_SECRET is not set.")
        }
        return secret || "mock-client-secret"
      })(),
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
  },
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        const email = user.email || ""
        try {
          const res = await fetch(backendUrl(`/internal/resolve-identity?email=${encodeURIComponent(email)}`), {
            headers: {
              "Content-Type": "application/json",
              "X-Internal-Secret": process.env.INTERNAL_RESOLVE_SECRET || ""
            }
          })
          
          if (res.ok) {
            const data = await res.json()
            user.role = data.role
            user.erpId = data.erp_id || data.erpId
            user.department = data.department || data.dept || ""
            user.currentYear = data.current_year ?? undefined
            user.currentSem = data.current_sem ?? undefined
            user.currentSec = data.current_sec ?? undefined
            user.facultyInitials = data.faculty_initials ?? undefined
            user.fullName = data.full_name ?? undefined
            return true
          } else {
            const errText = await res.text().catch(() => "")
            console.warn("[NextAuth] resolve-identity returned error:", res.status, errText)
          }
        } catch (err) {
          console.error("[NextAuth] SignIn callback lookup failed:", err)
        }

        // Resilient fallback for local dev / testing:
        // Provision a minimal identity so Google login succeeds.
        // Backend will infer year/sem from email pattern on first chat request.
        const cleanEmail = email.toLowerCase().trim()
        const erpId = "STU_" + (cleanEmail.split("@")[0] || "TEST").toUpperCase().replace(/[^A-Z0-9]/g, "_")
        user.role = "student"
        user.erpId = erpId
        user.department = "ICT"
        return true
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
        } else if (process.env.NODE_ENV === "development" && user.email === "demo.faculty@daiict.ac.in") {
          token.role = "faculty"
          token.erpId = "FAC123"
          token.department = "ICT"
        } else if (process.env.NODE_ENV === "development" && user.email === "demo.admin@dau.ac.in") {
          token.role = "admin"
          token.erpId = "ADM123"
          token.department = "IT"
        } else if (user.erpId) {
          token.role = user.role
          token.erpId = user.erpId
          token.department = user.department
          token.currentYear = user.currentYear
          token.currentSem = user.currentSem
          token.currentSec = user.currentSec
          token.facultyInitials = user.facultyInitials
          token.fullName = user.fullName
        } else {
          const erpData = await lookupErpIdentity(user.email)
          if (erpData) {
            token.role = erpData.role
            token.erpId = erpData.erpId
            token.department = erpData.department
            token.currentYear = erpData.currentYear
            token.currentSem = erpData.currentSem
            token.currentSec = erpData.currentSec
            token.facultyInitials = erpData.facultyInitials
            token.fullName = erpData.fullName
          }
        }
      }

      // Mint a fresh short-lived internal JWT on every token update
      if (token.role && token.erpId) {
        token.accessToken = signInternalJwt({
          role: token.role as "student" | "faculty" | "admin" | "guest",
          erpId: token.erpId,
          department: token.department || undefined,
          currentYear: token.currentYear,
          currentSem: token.currentSem,
          currentSec: token.currentSec,
          facultyInitials: token.facultyInitials,
          fullName: token.fullName,
        })
      }
      
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.role = token.role as "student" | "faculty" | "admin" | "guest"
        session.user.erpId = token.erpId as string
        session.user.department = token.department as string | undefined
        session.user.currentYear = token.currentYear as number | undefined
        session.user.currentSem = token.currentSem as number | undefined
        session.user.currentSec = token.currentSec as string | undefined
        session.user.fullName = token.fullName as string | undefined
      }
      session.accessToken = token.accessToken as string | undefined
      return session
    },
  },
  secret: (() => {
    const s = process.env.NEXTAUTH_SECRET
    if (!s) {
      if (process.env.NODE_ENV === "production" && !process.env.NEXT_PHASE) {
        console.warn("WARNING: NEXTAUTH_SECRET is not set.")
      }
      return "mock-nextauth-secret"
    }
    return s
  })(),
  pages: {
    signIn: "/login",
    error: "/login",
  },
}
