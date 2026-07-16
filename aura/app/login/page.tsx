"use client"

import { useState, Suspense } from "react"
import { signIn } from "next-auth/react"
import { useSearchParams } from "next/navigation"
import { Sparkles, Loader2, Globe, GraduationCap, BookOpen, AlertCircle, Shield } from "lucide-react"
import { BrandMark } from "@/components/common/BrandMark"

function LoginCard() {
  const [loading, setLoading] = useState<"google" | "demo-student" | "demo-faculty" | "demo-admin" | null>(null)
  const searchParams = useSearchParams()
  const errorParam = searchParams.get("error")

  let errorMsg: string | null = null
  if (errorParam === "NotRegistered") {
    errorMsg = "Your DAU account is not yet registered in AURA. Contact the administrator."
  } else if (errorParam === "DomainNotAllowed") {
    errorMsg = "Access restricted. You must log in with a @dau.ac.in or @daiict.ac.in email address."
  } else if (errorParam) {
    errorMsg = "Authentication failed. Please try again."
  }

  const handleGoogleSignIn = () => {
    setLoading("google")
    signIn("google", { callbackUrl: "/" })
  }

  const handleDemoSignIn = async (role: "student" | "faculty" | "admin") => {
    setLoading(`demo-${role}`)
    const email = role === "student"
      ? "demo.student@dau.ac.in"
      : role === "faculty"
        ? "demo.faculty@daiict.ac.in"
        : "demo.admin@dau.ac.in"
    const password = role === "student"
      ? "Student@123"
      : role === "faculty"
        ? "Faculty@123"
        : "Admin@123"

    try {
      const res = await signIn("credentials", {
        email,
        password,
        redirect: false,
        callbackUrl: "/",
      })
      if (res?.ok) {
        window.location.href = "/"
      } else {
        setLoading(null)
        alert(`Demo login failed: ${res?.error || "Unknown error"}`)
      }
    } catch {
      setLoading(null)
      alert("Network error during demo login")
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 shadow-2xl backdrop-blur-xl p-6">
      {errorMsg && (
        <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-theme-red/30 bg-theme-red/10 p-3.5 text-xs text-theme-red leading-relaxed">
          <AlertCircle className="size-4 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      <button
        onClick={handleGoogleSignIn}
        disabled={loading !== null}
        className="w-full flex items-center justify-center gap-2 rounded-xl bg-white text-black py-3 text-sm font-semibold transition-opacity hover:opacity-90 disabled:opacity-60 cursor-pointer"
      >
        {loading === "google" ? <Loader2 className="size-4 animate-spin" /> : <Globe className="size-4" />}
        Continue with Google Workspace
      </button>

      <p className="mt-4 text-center text-xs text-neutral-400">
        Must be an official @dau.ac.in or @daiict.ac.in email address.
      </p>

      {/* Development Demo Mode - always shown in dev build */}
      {/* Dev-only: after switching demo accounts, always wait for Sign Out to fully
          redirect to /login before clicking another demo button — rapid switching has a
          known session-cache race condition, tracked as a follow-up. */}
      {process.env.NODE_ENV === "development" && (
        <div className="mt-8 border-t border-theme-gray-light pt-6">
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => handleDemoSignIn("student")}
              disabled={loading !== null}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-theme-gray-lighter bg-theme-gray px-2 py-2 text-[11px] font-medium text-neutral-300 hover:text-white disabled:opacity-60 cursor-pointer"
            >
              {loading === "demo-student" ? <Loader2 className="size-3 animate-spin" /> : <GraduationCap className="size-3.5 text-theme-yellow" />}
              Student
            </button>
            <button
              onClick={() => handleDemoSignIn("faculty")}
              disabled={loading !== null}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-theme-gray-lighter bg-theme-gray px-2 py-2 text-[11px] font-medium text-neutral-300 hover:text-white disabled:opacity-60 cursor-pointer"
            >
              {loading === "demo-faculty" ? <Loader2 className="size-3 animate-spin" /> : <BookOpen className="size-3.5 text-theme-yellow" />}
              Faculty
            </button>
            <button
              onClick={() => handleDemoSignIn("admin")}
              disabled={loading !== null}
              className="flex items-center justify-center gap-1.5 rounded-lg border border-theme-gray-lighter bg-theme-gray px-2 py-2 text-[11px] font-medium text-neutral-300 hover:text-white disabled:opacity-60 cursor-pointer"
            >
              {loading === "demo-admin" ? <Loader2 className="size-3 animate-spin" /> : <Shield className="size-3.5 text-theme-yellow" />}
              Admin
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-theme-black px-4 py-10">
      {/* Background */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:24px_24px]" />
        <div className="absolute -left-32 -top-32 size-96 rounded-full bg-theme-red/20 blur-3xl" />
        <div className="absolute -bottom-32 -right-32 size-96 rounded-full bg-theme-yellow/20 blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        {/* Brand */}
        <div className="mb-8 flex flex-col items-center gap-3 text-center">
          <div className="flex items-center gap-2">
            <BrandMark className="size-10 text-base" />
            <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-2xl font-semibold text-transparent">
              AURA
            </span>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray px-3 py-1 text-xs text-neutral-400">
            <Sparkles className="size-3 text-theme-yellow" />
            DAU AI Assistant
          </span>
          <p className="mt-1 max-w-xs text-sm text-neutral-400">
            Sign in with your university account to personalise your experience.
          </p>
        </div>

        {/* Card wrapper in Suspense to avoid Next.js deopt */}
        <Suspense fallback={
          <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 shadow-2xl backdrop-blur-xl p-10 flex justify-center">
            <Loader2 className="animate-spin text-theme-yellow size-6" />
          </div>
        }>
          <LoginCard />
        </Suspense>

        <p className="mt-6 text-center text-xs text-neutral-600">
          Dhirubhai Ambani University · Gandhinagar, Gujarat
        </p>
      </div>
    </div>
  )
}
