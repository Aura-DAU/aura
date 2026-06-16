"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowLeft, GraduationCap, Users, AlertCircle, CheckCircle2 } from "lucide-react";
import { ThemeToggle } from "@/app/components/ThemeToggle";
import { LoginForm } from "./LoginForm";
import { RegisterForm } from "./RegisterForm";
import { DemoCredentials } from "./DemoCredentials";
import { UserSession } from "@/lib/api/auth.action";
import { StudentProfile } from "@/app/api/chat.service";

export default function LoginPage() {
  const router = useRouter();

  // Auth Modes: "signin" or "signup"
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  // Roles: "student" or "parent"
  const [role, setRole] = useState<"student" | "parent">("student");

  // Input states sync'd for demo filling
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  // Feedback states
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Clear inputs and messages when toggling modes or roles
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setEmail("");
    setPassword("");
    setErrorMsg(null);
    setSuccessMsg(null);
  }, [authMode, role]);

  const handleFillDemo = (demoType: "student" | "parent") => {
    setErrorMsg(null);
    setAuthMode("signin");
    if (demoType === "student") {
      setRole("student");
      setEmail("student@dau.ac.in");
      setPassword("password123");
    } else {
      setRole("parent");
      setEmail("parent@example.com");
      setPassword("password123");
    }
  };

  const handleLoginSuccess = (session: UserSession, profile: StudentProfile) => {
    // Save profile and redirect (the session cookie is already managed by Server Action)
    localStorage.setItem("aura_student_profile", JSON.stringify(profile));
    router.push("/");
  };

  return (
    <div className="min-h-screen w-full bg-slate-50 dark:bg-slate-950 flex flex-col relative overflow-hidden transition-colors duration-300 font-sans">
      {/* Decorative background gradients */}
      <div className="absolute top-[-15%] left-[-15%] w-[50%] h-[50%] rounded-full bg-brand-500/10 dark:bg-brand-500/20 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-15%] right-[-15%] w-[50%] h-[50%] rounded-full bg-blue-500/5 dark:bg-blue-500/10 blur-[120px] pointer-events-none" />

      <header className="absolute top-0 left-0 w-full p-6 flex justify-between items-center z-10">
        <Link
          href="/"
          className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Chat
        </Link>
        <ThemeToggle />
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6 z-10 my-16">
        <div className="w-full max-w-lg animate-in fade-in slide-in-from-bottom-4 duration-700">
          
          {/* Main Logo & Title */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-400 dark:from-brand-500 dark:to-brand-300 text-white shadow-xl shadow-brand-500/10 dark:shadow-brand-500/20 mb-4">
              <span className="text-2xl font-bold tracking-tight">A</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-1">
              {authMode === "signin" ? "Academic Portal Login" : "Create Academic Profile"}
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              {authMode === "signin"
                ? "Sign in to access student handbooks and curfew logs"
                : "Register to get personalized answers on exams and campus policies"}
            </p>
          </div>

          {/* Form Container */}
          <div className="backdrop-blur-xl bg-white/70 dark:bg-slate-900/70 border border-slate-200/60 dark:border-slate-800/60 p-6 sm:p-8 rounded-3xl shadow-xl shadow-slate-200/40 dark:shadow-black/40 relative overflow-hidden">
            
            {/* Sliding Role Selectors (Tabs) */}
            <div className="relative flex p-1 bg-slate-100 dark:bg-slate-950/70 rounded-xl mb-6 border border-slate-200/30 dark:border-slate-800/30">
              <button
                type="button"
                onClick={() => setRole("student")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all duration-200 z-10 ${
                  role === "student"
                    ? "bg-white dark:bg-slate-900 text-brand-700 dark:text-brand-400 shadow-md"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                <GraduationCap className="w-4 h-4" />
                Student
              </button>
              <button
                type="button"
                onClick={() => setRole("parent")}
                className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all duration-200 z-10 ${
                  role === "parent"
                    ? "bg-white dark:bg-slate-900 text-brand-700 dark:text-brand-400 shadow-md"
                    : "text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-slate-200"
                }`}
              >
                <Users className="w-4 h-4" />
                Parent
              </button>
            </div>

            {/* Error & Success Messages */}
            {errorMsg && (
              <div className="mb-5 flex items-start gap-2.5 bg-red-50 dark:bg-red-950/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-900/50 p-3.5 rounded-xl text-xs leading-relaxed animate-in fade-in slide-in-from-top-2">
                <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{errorMsg}</span>
              </div>
            )}

            {successMsg && (
              <div className="mb-5 flex items-start gap-2.5 bg-emerald-50 dark:bg-emerald-950/20 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-900/50 p-3.5 rounded-xl text-xs leading-relaxed animate-in fade-in slide-in-from-top-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
                <span>{successMsg}</span>
              </div>
            )}

            {/* Render Login or Register Form */}
            {authMode === "signin" ? (
              <LoginForm
                role={role}
                email={email}
                setEmail={setEmail}
                password={password}
                setPassword={setPassword}
                onSuccess={handleLoginSuccess}
                onError={setErrorMsg}
              />
            ) : (
              <RegisterForm
                role={role}
                onSuccess={(msg) => {
                  setSuccessMsg(msg);
                  setAuthMode("signin");
                }}
                onError={setErrorMsg}
              />
            )}

            {/* Toggle Sign In / Sign Up */}
            <div className="mt-6 text-center pt-4 border-t border-slate-100 dark:border-slate-800/40">
              <p className="text-xs text-slate-500 dark:text-slate-400">
                {authMode === "signin" ? (
                  <>
                    Logging in for the first time?{" "}
                    <button
                      type="button"
                      onClick={() => setAuthMode("signup")}
                      className="font-semibold text-brand-600 dark:text-brand-400 hover:underline cursor-pointer"
                    >
                      Create an account
                    </button>
                  </>
                ) : (
                  <>
                    Already have an account?{" "}
                    <button
                      type="button"
                      onClick={() => setAuthMode("signin")}
                      className="font-semibold text-brand-600 dark:text-brand-400 hover:underline cursor-pointer"
                    >
                      Sign in here
                    </button>
                  </>
                )}
              </p>
            </div>
          </div>

          {/* Quick-test Demo Credentials Card */}
          <DemoCredentials onFillDemo={handleFillDemo} />

          {/* IT Support footer */}
          <p className="text-center text-[11px] text-slate-400 dark:text-slate-500 mt-6 leading-normal">
            Security managed by Dhirubhai Ambani University IT Support.<br />
            For systemic login issues, contact the system administrator.
          </p>

        </div>
      </main>
    </div>
  );
}
