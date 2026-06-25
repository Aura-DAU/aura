"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, AlertCircle, CheckCircle2, Sparkles } from "lucide-react";
import { ThemeToggle } from "@/app/components/ThemeToggle";
import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";
import { DemoCredentials } from "./DemoCredentials";
import { UserSession } from "@/lib/api/auth.schema";
import { StudentProfile } from "@/app/api/chat.service";

export default function LoginPage() {
  const router = useRouter();

  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setEmail("");
    setPassword("");
    setErrorMsg(null);
    setSuccessMsg(null);
  }, [authMode]);

  const handleFillDemo = () => {
    setErrorMsg(null);
    setAuthMode("signin");
    setEmail("student@dau.ac.in");
    setPassword("password123");
  };

  const handleLoginSuccess = (_session: UserSession, profile: StudentProfile) => {
    localStorage.setItem("aura_student_profile", JSON.stringify(profile));
    router.push("/");
  };

  return (
    <div className="min-h-screen w-full bg-[var(--color-aura-lavender)] dark:bg-slate-950 flex flex-col relative overflow-hidden font-sans text-[var(--color-aura-ink)] dark:text-slate-100">
      {/* Sticker-pack background blobs */}
      <div className="pointer-events-none absolute -top-32 -left-32 w-[520px] h-[520px] rounded-full bg-brand-500/20 dark:bg-brand-500/15 blur-[80px]" />
      <div className="pointer-events-none absolute -bottom-40 -right-32 w-[460px] h-[460px] rounded-full bg-[var(--color-aura-yellow)]/45 dark:bg-[var(--color-aura-yellow)]/15 blur-[80px]" />
      <div className="pointer-events-none absolute top-12 right-24 w-44 h-44 rounded-full bg-[var(--color-aura-mint)]/60 dark:bg-[var(--color-aura-mint)]/20 blur-[40px]" />

      {/* Floating sticker shapes */}
      <div
        aria-hidden
        className="pointer-events-none absolute hidden sm:block top-32 left-12 w-20 h-20 rotate-12 animate-float"
      >
        <div className="w-full h-full rounded-3xl bg-[var(--color-aura-coral)] border-2 border-[var(--color-aura-ink)] shadow-sticker" />
      </div>
      <div
        aria-hidden
        className="pointer-events-none absolute hidden sm:block bottom-24 left-1/4 w-14 h-14 -rotate-12 animate-float"
        style={{ animationDelay: "1s" }}
      >
        <div className="w-full h-full rounded-2xl bg-[var(--color-aura-sky)] border-2 border-[var(--color-aura-ink)] shadow-sticker-sm" />
      </div>

      {/* Top bar */}
      <header className="relative z-10 w-full px-5 sm:px-10 py-5 flex justify-between items-center">
        <Link
          href="/"
          className="inline-flex items-center gap-2 rounded-full border-2 border-[var(--color-aura-ink)] bg-white px-4 py-2 text-xs font-bold text-[var(--color-aura-ink)] shadow-sticker-sm transition-transform hover:-translate-y-0.5 hover:translate-x-0 dark:bg-slate-900 dark:text-slate-100 dark:border-slate-100"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          back to chat
        </Link>
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 rounded-full border-2 border-[var(--color-aura-ink)] bg-white px-3 py-2 shadow-sticker-sm dark:bg-slate-900 dark:border-slate-100">
            <div className="grid place-items-center w-7 h-7 rounded-lg bg-[var(--color-aura-ink)] dark:bg-brand-500">
              <span className="font-black text-sm text-[var(--color-aura-yellow)]">A</span>
            </div>
            <span className="font-black tracking-tight text-sm">AURA</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      <main className="relative z-10 flex-1 flex flex-col items-center justify-center px-5 sm:px-6 pb-12">
        <div className="w-full max-w-lg">
          {/* Hero */}
          <div className="text-center mb-6 sm:mb-8">
            <span className="inline-flex items-center gap-1.5 rounded-full border-2 border-[var(--color-aura-ink)] bg-[var(--color-aura-yellow)] px-3 py-1 text-[10px] font-black uppercase tracking-wider shadow-sticker-sm">
              <Sparkles className="w-3 h-3" />
              DAU academic portal
            </span>
            <h1 className="mt-5 text-[44px] sm:text-[56px] font-black leading-[0.95] tracking-[-0.03em] text-[var(--color-aura-ink)] dark:text-white">
              {authMode === "signin" ? (
                <>
                  hey future
                  <br />
                  engineer <span className="inline-block animate-wiggle origin-bottom">👋</span>
                </>
              ) : (
                <>
                  let&apos;s get
                  <br />
                  you set up <span className="inline-block animate-wiggle origin-bottom">🚀</span>
                </>
              )}
            </h1>
            <p className="mt-3 sm:mt-4 text-sm sm:text-[15px] leading-relaxed text-slate-600 dark:text-slate-300 max-w-md mx-auto">
              {authMode === "signin"
                ? "sign in to AURA for exams, curfews, hostel rules & campus chaos — instantly."
                : "register to get personalised answers on exams, policies & everything DAU."}
            </p>
          </div>

          {/* Sticker auth card */}
          <div className="rounded-3xl border-2 border-[var(--color-aura-ink)] bg-white shadow-sticker-lg dark:bg-slate-900 dark:border-slate-100 p-6 sm:p-7">

            {errorMsg && (
              <div className="mb-4 flex items-start gap-2.5 rounded-2xl border-2 border-[var(--color-aura-ink)] bg-[var(--color-aura-coral)]/90 text-[var(--color-aura-ink)] p-3.5 text-xs font-semibold leading-relaxed shadow-sticker-sm">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {successMsg && (
              <div className="mb-4 flex items-start gap-2.5 rounded-2xl border-2 border-[var(--color-aura-ink)] bg-[var(--color-aura-mint)] text-[var(--color-aura-ink)] p-3.5 text-xs font-semibold leading-relaxed shadow-sticker-sm">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{successMsg}</span>
              </div>
            )}

            {authMode === "signin" ? (
              <LoginForm
                email={email}
                setEmail={setEmail}
                password={password}
                setPassword={setPassword}
                onSuccess={handleLoginSuccess}
                onError={setErrorMsg}
              />
            ) : (
              <RegisterForm
                onSuccess={(msg) => {
                  setSuccessMsg(msg);
                  setAuthMode("signin");
                }}
                onError={setErrorMsg}
              />
            )}

            <div className="mt-5 pt-4 border-t-2 border-dashed border-slate-200 dark:border-slate-700 text-center">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {authMode === "signin" ? (
                  <>
                    first time here?{" "}
                    <button
                      type="button"
                      onClick={() => setAuthMode("signup")}
                      className="font-black text-brand-600 dark:text-brand-300 underline decoration-2 decoration-[var(--color-aura-yellow)] underline-offset-2 hover:decoration-[var(--color-aura-coral)] cursor-pointer"
                    >
                      create an account
                    </button>
                  </>
                ) : (
                  <>
                    already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => setAuthMode("signin")}
                      className="font-black text-brand-600 dark:text-brand-300 underline decoration-2 decoration-[var(--color-aura-yellow)] underline-offset-2 hover:decoration-[var(--color-aura-coral)] cursor-pointer"
                    >
                      sign in here
                    </button>
                  </>
                )}
              </p>
            </div>
          </div>

          <DemoCredentials onFillDemo={handleFillDemo} />

          <p className="text-center text-[11px] font-medium text-slate-500 dark:text-slate-500 mt-6">
            🔐 managed by DAU IT  ·  v1.0
          </p>
        </div>
      </main>
    </div>
  );
}
