"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  Eye,
  EyeOff,
  Info,
  Loader2,
  Sparkles,
} from "lucide-react"
import { BrandMark } from "@/components/common/BrandMark"
import { cn } from "@/lib/utils"

const SESSION_KEY  = "aura-session-v1"
const THREADS_KEY  = "aura-threads-v2"

// ─── Demo credentials (shown in UI only) ─────────────────────────────────────
const DEMO = {
  email: "demo.student@dau.ac.in",
  password: "Student@123",
} as const

// ─── Types ───────────────────────────────────────────────────────────────────
type Tab = "signin" | "signup"

// ─── Component ───────────────────────────────────────────────────────────────
export default function LoginPage() {
  const router = useRouter()

  const [tab, setTab] = useState<Tab>("signin")
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [form, setForm] = useState({ name: "", email: "", password: "", confirm: "" })

  const reset = () => {
    setForm({ name: "", email: "", password: "", confirm: "" })
    setError(null)
    setSuccess(false)
  }

  const handleTabChange = (t: Tab) => { setTab(t); reset() }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setError(null)
  }

  const fillDemo = () => {
    setForm((prev) => ({ ...prev, email: DEMO.email, password: DEMO.password, confirm: DEMO.password }))
    setError(null)
  }

  // ── Validation ──────────────────────────────────────────────────────────────
  const validate = (): string | null => {
    if (tab === "signup" && !form.name.trim()) return "Please enter your full name."
    if (!form.email || !form.password) return "Please fill in all fields."
    if (!form.email.toLowerCase().endsWith("@dau.ac.in"))
      return "Student email must end with @dau.ac.in"
    if (tab === "signup") {
      if (form.password.length < 8) return "Password must be at least 8 characters."
      if (form.password !== form.confirm) return "Passwords do not match."
    }
    return null
  }

  // ── Submit ──────────────────────────────────────────────────────────────────
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const err = validate()
    if (err) { setError(err); return }

    setLoading(true)

    if (tab === "signin") {
      try {
        const res  = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: form.email, password: form.password, role: "student" }),
        })
        const data = await res.json() as { name?: string; email?: string; role?: string; threads?: unknown[]; error?: string }
        if (!res.ok) {
          setError(data.error ?? "Invalid email or password.")
        } else {
          localStorage.setItem(SESSION_KEY, JSON.stringify({ name: data.name, email: data.email, role: data.role }))
          // Seed chat history returned from server
          if (Array.isArray(data.threads) && data.threads.length > 0) {
            localStorage.setItem(THREADS_KEY, JSON.stringify(data.threads))
          }
          setSuccess(true)
          window.location.href = "/"
        }
      } catch {
        setError("Network error. Please try again.")
      }
    } else {
      try {
        const res  = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: form.name.trim(), email: form.email, password: form.password, role: "student" }),
        })
        const data = await res.json() as { name?: string; email?: string; role?: string; error?: string }
        if (!res.ok) {
          setError(data.error ?? "Registration failed.")
        } else {
          localStorage.setItem(SESSION_KEY, JSON.stringify({ name: data.name, email: data.email, role: data.role }))
          setSuccess(true)
          window.location.href = "/"
        }
      } catch {
        setError("Network error. Please try again.")
      }
    }

    setLoading(false)
  }

  // ── Render ──────────────────────────────────────────────────────────────────
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
            {tab === "signin"
              ? "Sign in to personalise your experience and save your conversations."
              : "Create an account to get started with AURA."}
          </p>
        </div>

        {/* Card */}
        <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 shadow-2xl backdrop-blur-xl">

          {/* Sign In / Sign Up tabs */}
          <div className="flex border-b border-theme-gray-light">
            {(["signin", "signup"] as Tab[]).map((t) => (
              <button
                key={t}
                type="button"
                id={`tab-${t}`}
                onClick={() => handleTabChange(t)}
                className={cn(
                  "flex-1 py-3.5 text-sm font-medium transition-colors",
                  tab === t
                    ? "border-b-2 border-theme-red text-neutral-100"
                    : "text-neutral-400 hover:text-neutral-200"
                )}
              >
                {t === "signin" ? "Sign In" : "Sign Up"}
              </button>
            ))}
          </div>

          {/* Domain hint */}
          <div className="flex items-center gap-2 border-b border-theme-gray-light bg-theme-gray-light/30 px-5 py-2.5 text-xs text-neutral-400">
            <Info className="size-3.5 shrink-0 text-theme-yellow" />
            Students must use their official @dau.ac.in email address.
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-6">

            {/* Name — Sign Up only */}
            {tab === "signup" && (
              <InputField
                id="auth-name"
                label="Full Name"
                name="name"
                type="text"
                placeholder="Your full name"
                value={form.name}
                onChange={handleChange}
                autoComplete="name"
              />
            )}

            {/* Email */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="auth-email" className="text-xs font-medium text-neutral-300">
                Email
                <span className="ml-1.5 rounded bg-theme-red/20 px-1.5 py-0.5 text-[10px] font-normal text-theme-red">
                  @dau.ac.in only
                </span>
              </label>
              <input
                id="auth-email"
                name="email"
                type="email"
                placeholder="you@dau.ac.in"
                value={form.email}
                onChange={handleChange}
                autoComplete="email"
                className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3.5 py-2.5 text-sm text-neutral-100 placeholder:text-neutral-500 outline-none transition-colors focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
              />
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1.5">
              <label htmlFor="auth-password" className="text-xs font-medium text-neutral-300">
                Password
              </label>
              <div className="relative">
                <input
                  id="auth-password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={form.password}
                  onChange={handleChange}
                  autoComplete={tab === "signin" ? "current-password" : "new-password"}
                  className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3.5 py-2.5 pr-10 text-sm text-neutral-100 placeholder:text-neutral-500 outline-none transition-colors focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
                />
                <button
                  type="button"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-400 transition-colors hover:text-neutral-200"
                >
                  {showPassword ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                </button>
              </div>
            </div>

            {/* Confirm Password — Sign Up only */}
            {tab === "signup" && (
              <div className="flex flex-col gap-1.5">
                <label htmlFor="auth-confirm" className="text-xs font-medium text-neutral-300">
                  Confirm Password
                </label>
                <input
                  id="auth-confirm"
                  name="confirm"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={form.confirm}
                  onChange={handleChange}
                  autoComplete="new-password"
                  className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3.5 py-2.5 text-sm text-neutral-100 placeholder:text-neutral-500 outline-none transition-colors focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
                />
              </div>
            )}

            {/* Forgot password — Sign In only */}
            {tab === "signin" && (
              <div className="text-right">
                <button
                  type="button"
                  className="text-xs text-neutral-400 underline-offset-2 transition-colors hover:text-theme-yellow hover:underline"
                >
                  Forgot password?
                </button>
              </div>
            )}

            {/* Error */}
            {error && (
              <p
                role="alert"
                className="rounded-lg border border-theme-red/30 bg-theme-red/10 px-3 py-2 text-xs text-theme-red"
              >
                {error}
              </p>
            )}

            {/* Submit */}
            <button
              id="auth-submit"
              type="submit"
              disabled={loading || success}
              className="mt-1 flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-theme-red to-theme-yellow py-2.5 text-sm font-semibold text-black transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {loading ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  {tab === "signin" ? "Signing in…" : "Creating account…"}
                </>
              ) : success ? (
                "Welcome! Redirecting…"
              ) : tab === "signin" ? (
                "Sign In"
              ) : (
                "Create Account"
              )}
            </button>
          </form>

          {/* Demo credentials — Sign In only */}
          {tab === "signin" && (
            <div className="mx-6 mb-5 overflow-hidden rounded-xl border border-theme-yellow/20 bg-theme-yellow/5">
              <div className="flex items-center justify-between border-b border-theme-yellow/20 px-3.5 py-2">
                <span className="flex items-center gap-1.5 text-xs font-medium text-theme-yellow">
                  <Sparkles className="size-3" />
                  Demo credentials
                </span>
                <button
                  type="button"
                  id="fill-demo"
                  onClick={fillDemo}
                  className="rounded-md bg-theme-yellow/10 px-2.5 py-1 text-[11px] font-medium text-theme-yellow transition-colors hover:bg-theme-yellow/20"
                >
                  Auto-fill
                </button>
              </div>
              <div className="grid grid-cols-2 gap-x-3 gap-y-1 px-3.5 py-2.5 text-[11px] text-neutral-400">
                <span className="text-neutral-500">Email</span>
                <span className="break-all font-mono text-neutral-300">{DEMO.email}</span>
                <span className="text-neutral-500">Password</span>
                <span className="font-mono text-neutral-300">{DEMO.password}</span>
              </div>
            </div>
          )}

          {/* Guest */}
          <div className="border-t border-theme-gray-light px-6 py-4">
            <button
              type="button"
              id="login-guest"
              onClick={() => { router.refresh(); window.location.href = "/"; }}
              className="w-full rounded-xl border border-theme-gray-lighter py-2.5 text-sm text-neutral-400 transition-colors hover:border-neutral-500 hover:text-neutral-200"
            >
              Continue as Guest
            </button>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-neutral-600">
          Dhirubhai Ambani University · Gandhinagar, Gujarat
        </p>
      </div>
    </div>
  )
}

// ─── Reusable field ───────────────────────────────────────────────────────────
interface InputFieldProps {
  id: string
  label: string
  name: string
  type: string
  placeholder: string
  value: string
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  autoComplete?: string
}

function InputField({ id, label, name, type, placeholder, value, onChange, autoComplete }: InputFieldProps) {
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className="text-xs font-medium text-neutral-300">
        {label}
      </label>
      <input
        id={id}
        name={name}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        autoComplete={autoComplete}
        className="w-full rounded-xl border border-theme-gray-lighter bg-theme-gray-light px-3.5 py-2.5 text-sm text-neutral-100 placeholder:text-neutral-500 outline-none transition-colors focus:border-theme-red/60 focus:ring-2 focus:ring-theme-red/20"
      />
    </div>
  )
}
