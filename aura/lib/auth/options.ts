import { NextAuthOptions, DefaultSession } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import { backendUrl } from "@/lib/api/backend"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    user: {
      role: "student" | "faculty" | "admin"
      erpId: string
      department?: string
    } & DefaultSession["user"]
  }

  interface User {
    role?: "student" | "faculty" | "admin"
    erpId?: string
    department?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: "student" | "faculty" | "admin"
    erpId?: string
    department?: string
    accessToken?: string
  }
}

/**
 * Fetches the user's ERP Identity from the backend Auth DB.
 */
async function lookupErpIdentity(email: string): Promise<{ role: "student" | "faculty" | "admin"; erpId: string; department: string } | null> {
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
      department: data.department || data.dept || ""
    }
  } catch (error) {
    console.error("[NextAuth] Error calling lookup endpoint:", error)
    return null
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID || "mock-client-id",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "mock-client-secret",
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
        if (!email.endsWith("@dau.ac.in") && !email.endsWith("@daiict.ac.in")) {
          return "/login?error=DomainNotAllowed"
        }
        
        try {
          const res = await fetch(backendUrl(`/internal/resolve-identity?email=${encodeURIComponent(email)}`), {
            headers: {
              "Content-Type": "application/json",
              "X-Internal-Secret": process.env.INTERNAL_RESOLVE_SECRET || ""
            }
          })
          
          if (res.status === 404) {
            return "/login?error=NotRegistered"
          }
          if (!res.ok) {
            return "/login?error=ServerError"
          }
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
        if (user.email === "demo.student@dau.ac.in") {
          token.role = "student"
          token.erpId = "DEMO123"
          token.department = "ICT"
        } else if (user.email === "demo.faculty@daiict.ac.in") {
          token.role = "faculty"
          token.erpId = "FAC123"
          token.department = "ICT"
        } else {
          const erpData = await lookupErpIdentity(user.email)
          if (erpData) {
            token.role = erpData.role
            token.erpId = erpData.erpId
            token.department = erpData.department
          }
        }
      }

      // Mint a fresh short-lived internal JWT on every token update
      if (token.role && token.erpId) {
        token.accessToken = signInternalJwt({
          role: token.role as "student" | "faculty" | "admin",
          erpId: token.erpId,
          department: token.department || undefined,
        })
      }
      
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.role = token.role as "student" | "faculty" | "admin"
        session.user.erpId = token.erpId as string
        session.user.department = token.department as string | undefined
      }
      session.accessToken = token.accessToken
      return session
    },
  },
  secret: process.env.NEXTAUTH_SECRET || "fallback-secret-for-development-only",
  pages: {
    signIn: "/login",
    error: "/login",
  },
}
