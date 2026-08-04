"use client"

import { useState, Suspense, useEffect } from "react"
import Link from "next/link"
import { signIn } from "next-auth/react"
import { useSearchParams } from "next/navigation"
import { Sparkles, Loader2, GraduationCap, BookOpen, AlertCircle, Shield } from "lucide-react"
import { AnimatedBrandMark } from "@/components/ui/animated-brand-mark"
import { AuroraBackground } from "@/components/ui/aurora-background"
import { toastError } from "@/lib/toast"

function GoogleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 48 48" aria-hidden="true">
      <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
      <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
      <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
      <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
    </svg>
  )
}

function LoginCard() {
  const [loading, setLoading] = useState<"google" | "demo-student" | "demo-faculty" | "demo-admin" | null>(null)
  const searchParams = useSearchParams()
  const errorParam = searchParams.get("error")

  let errorMsg: string | null = null
  if (errorParam === "NotRegistered") {
    errorMsg = "Your DAU account is not yet registered in AURA. Contact the administrator."
  } else if (errorParam === "DomainNotAllowed") {
    errorMsg = "Access restricted. Sign in requires an official @dau.ac.in email address. Use \"Continue as Guest\" instead."
  } else if (errorParam) {
    errorMsg = "Authentication failed. Please try again."
  }

  useEffect(() => {
    if (errorMsg) toastError(errorMsg)
  }, [errorMsg])

  const handleGoogleSignIn = async () => {
    setLoading("google")
    try {
      await signIn("google", { callbackUrl: "/" })
    } catch {
      toastError("Could not start Google sign-in. Please try again.")
      setLoading(null)
    }
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
        toastError(`Demo login failed: ${res?.error || "Unknown error"}`)
      }
    } catch {
      setLoading(null)
      toastError("Network error during demo login")
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 p-6 shadow-2xl shadow-black/40 backdrop-blur-xl ring-1 ring-white/5">
      {errorMsg && (
        <div className="mb-4 flex items-start gap-2.5 rounded-xl border border-theme-red/30 bg-theme-red/10 p-3.5 text-xs text-theme-red leading-relaxed">
          <AlertCircle className="size-4 shrink-0 mt-0.5" />
          <span>{errorMsg}</span>
        </div>
      )}

      <button
        onClick={handleGoogleSignIn}
        disabled={loading !== null}
        className="w-full flex cursor-pointer items-center justify-center gap-2 rounded-xl bg-white py-3 text-sm font-semibold text-black transition-all hover:opacity-90 hover:shadow-[0_0_24px_-8px_rgba(255,255,255,0.35)] disabled:opacity-60"
      >
        {loading === "google" ? <Loader2 className="size-4 animate-spin" /> : <GoogleIcon className="size-4" />}
        Continue with Google Workspace
      </button>

      <p className="mt-4 text-center text-xs text-neutral-400">
        Must be an official @dau.ac.in email address.
      </p>

      <div className="mt-5 flex items-center gap-3 text-[11px] text-neutral-600">
        <div className="h-px flex-1 bg-theme-gray-light" />
        or
        <div className="h-px flex-1 bg-theme-gray-light" />
      </div>

      <Link
        href="/api/auth/guest"
        className="mt-5 flex w-full cursor-pointer items-center justify-center rounded-xl border border-theme-gray-lighter bg-transparent py-3 text-sm font-medium text-neutral-300 transition-all hover:border-neutral-500 hover:text-white"
      >
        Continue as Guest
      </Link>
      <p className="mt-2 text-center text-xs text-neutral-500">
        Guests get 10 questions/day. Sign in for unlimited access.
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
      {/* Background: minimal ambient aurora + a warm focal bloom, framed by a vignette. */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <AuroraBackground className="absolute inset-0 opacity-70" showRadialGradient={false} />
        {/* Warm bloom behind the card for focus. */}
        <div className="absolute left-1/2 top-1/2 size-[560px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(244,80,59,0.14),transparent_68%)] blur-2xl" />
        {/* Vignette to deepen the edges and draw focus to the sign-in card. */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,transparent_28%,rgba(0,0,0,0.62))]" />
      </div>

      <div className="relative z-10 w-full max-w-md">
        {/* Brand */}
        <div className="mb-8 flex flex-col items-center gap-3 text-center animate-in fade-in zoom-in-95 duration-500">
          <div className="flex items-center gap-2.5">
            <AnimatedBrandMark className="size-12 shadow-[0_0_36px_-6px_rgba(244,80,59,0.55)]" />
            <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text text-3xl font-semibold tracking-tight text-transparent">
              AURA
            </span>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full border border-theme-gray-light bg-theme-gray/80 px-3 py-1 text-xs text-neutral-400 backdrop-blur">
            <Sparkles className="size-3 text-theme-yellow" />
            DAU AI Assistant
          </span>
          <p className="mt-1 max-w-xs text-sm leading-relaxed text-neutral-400">
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
