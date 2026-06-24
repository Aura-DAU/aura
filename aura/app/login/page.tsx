"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import {
  Eye,
  EyeOff,
  Info,
  Loader2,
  Sparkles,
  GraduationCap,
  BookOpen,
  Mail,
} from "lucide-react"
import { BrandMark } from "@/components/common/BrandMark"
import { cn } from "@/lib/utils"

const SESSION_KEY = "aura-session-v1"
const THREADS_KEY = "aura-threads-v2"

// ─── Demo credentials ─────────────────────────────────────────────────────────
const DEMO_STUDENT = {
  email: "demo.student@dau.ac.in",
  password: "Student@123",
} as const

const DEMO_FACULTY = {
  email: "demo.faculty@daiict.ac.in",
  password: "Faculty@123",
} as const

// ─── Types ───────────────────────────────────────────────────────────────────
type Tab = "signin" | "signup"
type Role = "student" | "faculty"

interface RoleConfig {
  label: string
  domain: string
  domainHint: string
  icon: React.ReactNode
}

const ROLE_CONFIG: Record<Role, RoleConfig> = {
  student: {
    label: "Student",
    domain: "@dau.ac.in",
    domainHint: "Students must use their official @dau.ac.in address.",
    icon: <GraduationCap className="size-3.5" />,
  },
  faculty: {
    label: "Faculty",
    domain: "@daiict.ac.in",
    domainHint: "Faculty must use their official @daiict.ac.in address.",
    icon: <BookOpen className="size-3.5" />,
  },
}

// ─── Component ───────────────────────────────────────────────────────────────
export default function LoginPage() {
  const router = useRouter()

  const [role, setRole] = useState<Role>("student")
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

  const handleRoleChange = (r: Role) => {
    setRole(r)
    reset()
    // Faculty has no self-service sign-up — force signin tab
    if (r === "faculty") setTab("signin")
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }))
    setError(null)
  }

  const fillDemo = (demo: { email: string; password: string }, demoRole: Role) => {
    handleRoleChange(demoRole)
    setForm((prev) => ({ ...prev, email: demo.email, password: demo.password, confirm: demo.password }))
    setError(null)
    setTab("signin")
  }

  // ── Validation ──────────────────────────────────────────────────────────────
  const validate = (): string | null => {
    const { domain, label } = ROLE_CONFIG[role]
    if (tab === "signup" && !form.name.trim()) return "Please enter your full name."
    if (!form.email || !form.password) return "Please fill in all fields."
    if (!form.email.toLowerCase().endsWith(domain))
      return `${label} email must end with ${domain}`
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
        const res = await fetch("/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email: form.email, password: form.password, role }),
        })
        const data = await res.json() as { name?: string; email?: string; role?: string; threads?: unknown[]; error?: string }
        if (!res.ok) {
          setError(data.error ?? "Invalid email or password.")
          setLoading(false)
        } else {
          localStorage.setItem(SESSION_KEY, JSON.stringify({ name: data.name, email: data.email, role: data.role }))
          if (Array.isArray(data.threads) && data.threads.length > 0) {
            localStorage.setItem(THREADS_KEY, JSON.stringify(data.threads))
          }
          setSuccess(true)
          // Note: setLoading(false) intentionally omitted here — navigation fires immediately.
          window.location.href = "/"
        }
      } catch {
        setError("Network error. Please try again.")
        setLoading(false)
      }
    } else {
      // Sign-up — student only; faculty accounts are IT-provisioned
      try {
        const res = await fetch("/api/auth/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name: form.name.trim(), email: form.email, password: form.password, role }),
        })
        const data = await res.json() as { name?: string; email?: string; role?: string; error?: string }
        if (!res.ok) {
          setError(data.error ?? "Registration failed.")
          setLoading(false)
        } else {
          localStorage.setItem(SESSION_KEY, JSON.stringify({ name: data.name, email: data.email, role: data.role }))
          setSuccess(true)
          window.location.href = "/"
        }
      } catch {
        setError("Network error. Please try again.")
        setLoading(false)
      }
    }
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
              : "Create a student account to get started with AURA."}
          </p>
        </div>

        {/* Role selector */}
        <div className="mb-3 flex gap-2">
          {(Object.entries(ROLE_CONFIG) as [Role, RoleConfig][]).map(([r, cfg]) => (
            <button
              key={r}
              type="button"
              id={`role-${r}`}
              onClick={() => handleRoleChange(r)}
              className={cn(
                "flex flex-1 items-center justify-center gap-1.5 rounded-xl border py-2 text-xs font-medium transition-colors",
                role === r
                  ? "border-theme-red/60 bg-theme-red/10 text-theme-red"
                  : "border-theme-gray-lighter bg-theme-gray text-neutral-400 hover:border-neutral-500 hover:text-neutral-200"
              )}
            >
              {cfg.icon}
              {cfg.label}
            </button>
          ))}
        </div>

        {/* Card */}
        <div className="overflow-hidden rounded-2xl border border-theme-gray-light bg-theme-gray/80 shadow-2xl backdrop-blur-xl">

          {/* Sign In / Sign Up tabs — student only */}
          {role === "student" && (
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
          )}

          {/* Domain hint */}
          <div className="flex items-center gap-2 border-b border-theme-gray-light bg-theme-gray-light/30 px-5 py-2.5 text-xs text-neutral-400">
            <Info className="size-3.5 shrink-0 text-theme-yellow" />
            {ROLE_CONFIG[role].domainHint}
          </div>

          {/* Faculty — IT-provisioned accounts, show contact instead of sign-up form */}
          {role === "faculty" && tab === "signup" ? (
            <div className="flex flex-col items-center gap-3 px-6 py-8 text-center">
              <div className="flex size-12 items-center justify-center rounded-full bg-theme-yellow/10">
                <Mail className="size-5 text-theme-yellow" />
              </div>
              <p className="text-sm font-medium text-neutral-200">Faculty accounts are provisioned by IT</p>
              <p className="max-w-xs text-xs text-neutral-400">
                To request an AURA faculty account, contact the IT helpdesk at{" "}
                <a
                  href="mailto:ict-support@daiict.ac.in"
                  className="text-theme-yellow underline underline-offset-2 hover:opacity-80"
                >
                  ict-support@daiict.ac.in
                </a>
              </p>
              <button
                type="button"
                onClick={() => setTab("signin")}
                className="mt-2 text-xs text-neutral-400 underline-offset-2 hover:text-neutral-200 hover:underline"
              >
                Already have an account? Sign in
              </button>
            </div>
          ) : (
            /* Auth form */
            <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-6">

              {/* Name — sign-up only */}
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
                    {ROLE_CONFIG[role].domain} only
                  </span>
                </label>
                <input
                  id="auth-email"
                  name="email"
                  type="email"
                  placeholder={`you${ROLE_CONFIG[role].domain}`}
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

              {/* Confirm password — sign-up only */}
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

              {/* Forgot password — sign-in only */}
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
          )}

          {/* Demo credentials panel — sign-in only */}
          {tab === "signin" && (
            <div className="mx-6 mb-5 overflow-hidden rounded-xl border border-theme-yellow/20 bg-theme-yellow/5">
              <div className="flex items-center border-b border-theme-yellow/20 px-3.5 py-2">
                <span className="flex items-center gap-1.5 text-xs font-medium text-theme-yellow">
                  <Sparkles className="size-3" />
                  Demo credentials
                </span>
              </div>

              {/* Student demo row */}
              <div className="flex items-center justify-between border-b border-theme-yellow/10 px-3.5 py-2.5">
                <div className="flex items-center gap-2">
                  <GraduationCap className="size-3.5 shrink-0 text-neutral-500" />
                  <span className="font-mono text-[11px] text-neutral-300">{DEMO_STUDENT.email}</span>
                </div>
                <button
                  type="button"
                  id="fill-demo-student"
                  onClick={() => fillDemo(DEMO_STUDENT, "student")}
                  className="rounded-md bg-theme-yellow/10 px-2.5 py-1 text-[11px] font-medium text-theme-yellow transition-colors hover:bg-theme-yellow/20"
                >
                  Fill
                </button>
              </div>

              {/* Faculty demo row */}
              <div className="flex items-center justify-between px-3.5 py-2.5">
                <div className="flex items-center gap-2">
                  <BookOpen className="size-3.5 shrink-0 text-neutral-500" />
                  <span className="font-mono text-[11px] text-neutral-300">{DEMO_FACULTY.email}</span>
                </div>
                <button
                  type="button"
                  id="fill-demo-faculty"
                  onClick={() => fillDemo(DEMO_FACULTY, "faculty")}
                  className="rounded-md bg-theme-yellow/10 px-2.5 py-1 text-[11px] font-medium text-theme-yellow transition-colors hover:bg-theme-yellow/20"
                >
                  Fill
                </button>
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
              Browse as Guest{" "}
              <span className="text-neutral-600">(no history saved)</span>
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
