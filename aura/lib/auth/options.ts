import { NextAuthOptions, DefaultSession } from "next-auth"
import GoogleProvider from "next-auth/providers/google"
import CredentialsProvider from "next-auth/providers/credentials"

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
 * Temporary mock function to simulate fetching ERP Identity from the unbuilt backend.
 * In the future, this will call the backend API (e.g., AURA Auth DB) to get the true ERP mapping.
 */
async function lookupErpIdentity(email: string): Promise<{ role: "student" | "faculty" | "admin"; erpId: string; department: string } | null> {
  // Temporary mock logic based on domain
  if (email.endsWith("@dau.ac.in")) {
    return { role: "student", erpId: "202300000", department: "ICT" }
  } else if (email.endsWith("@daiict.ac.in")) {
    return { role: "faculty", erpId: "EMP9999", department: "ICT" }
  }
  return null
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
        const erpData = await lookupErpIdentity(user.email)
        if (erpData) {
          token.role = erpData.role
          token.erpId = erpData.erpId
          token.department = erpData.department
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
