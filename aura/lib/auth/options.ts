import { NextAuthOptions, DefaultSession } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import { backendUrl } from "@/lib/api/backend"

declare module "next-auth" {
  interface Session {
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
  }
}

/**
 * Fetches the user's ERP Identity from the backend Auth DB.
 */
async function lookupErpIdentity(email: string): Promise<{ role: "student" | "faculty" | "admin"; erpId: string; department: string } | null> {
  try {
    const res = await fetch(backendUrl(`/auth/lookup?email=${encodeURIComponent(email)}`), {
      headers: {
        "Content-Type": "application/json"
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
    async signIn({ user, account, profile }) {
      if (account?.provider === "google") {
        const email = user.email || ""
        if (email.endsWith("@dau.ac.in") || email.endsWith("@daiict.ac.in")) {
          return true
        }
        return false // Reject other domains
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
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.role = token.role as "student" | "faculty" | "admin"
        session.user.erpId = token.erpId as string
        session.user.department = token.department as string | undefined
      }
      return session
    },
  },
  secret: process.env.NEXTAUTH_SECRET || "fallback-secret-for-development-only",
  pages: {
    signIn: "/login",
    error: "/login",
  },
}
