import { NextAuthOptions, DefaultSession } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"
import { backendUrl } from "@/lib/api/backend"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import {
  getNextAuthSecret,
  requireGoogleOAuthCredentials,
  requireInternalResolveSecret,
} from "@/lib/auth/secrets"

declare module "next-auth" {
  interface Session {
    accessToken?: string
    user: {
      role: "student" | "faculty" | "admin" | "guest"
      erpId: string
      department?: string
    } & DefaultSession["user"]
  }

  interface User {
    role?: "student" | "faculty" | "admin" | "guest"
    erpId?: string
    department?: string
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: "student" | "faculty" | "admin" | "guest"
    erpId?: string
    department?: string
    accessToken?: string
  }
}

/**
 * Fetches the user's ERP Identity from the backend Auth DB.
 */
async function lookupErpIdentity(email: string): Promise<{ role: "student" | "faculty" | "admin" | "guest"; erpId: string; department: string } | null> {
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
      department: data.department || data.dept || ""
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
  },
  callbacks: {
    async signIn({ user, account }) {
      if (account?.provider === "google") {
        const email = user.email || ""
        if (!email.endsWith("@dau.ac.in") && !email.endsWith("@daiict.ac.in")) {
          user.role = "guest"
          user.erpId = "GUEST"
          user.department = "GUEST"
          return true
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
          role: token.role as "student" | "faculty" | "admin" | "guest",
          erpId: token.erpId,
          department: token.department || undefined,
          email: typeof token.email === "string" ? token.email : undefined,
        })
      }
      
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.role = token.role as "student" | "faculty" | "admin" | "guest"
        session.user.erpId = token.erpId as string
        session.user.department = token.department as string | undefined
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
