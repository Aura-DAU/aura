"use client";

import React, { useState } from "react";
import { Mail, Lock, Loader2, Eye, EyeOff, ArrowRight } from "lucide-react";
import { login } from "@/lib/api/auth.action";
import { LoginSchema, UserSession } from "@/lib/api/auth.schema";
import { StudentProfile } from "@/app/api/chat.service";

interface LoginFormProps {
  role: "student" | "parent";
  email: string;
  setEmail: (email: string) => void;
  password: string;
  setPassword: (password: string) => void;
  onSuccess: (session: UserSession, profile: StudentProfile) => void;
  onError: (msg: string | null) => void;
}

const inputBase =
  "w-full pl-10 pr-4 py-3 text-sm font-medium bg-white dark:bg-slate-950 border-2 border-[var(--color-aura-ink)] dark:border-slate-100 rounded-2xl text-[var(--color-aura-ink)] dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:translate-x-[2px] focus:translate-y-[2px] focus:shadow-none shadow-sticker-sm transition-all";

export function LoginForm({
  role,
  email,
  setEmail,
  password,
  setPassword,
  onSuccess,
  onError,
}: LoginFormProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onError(null);

    const validation = LoginSchema.safeParse({ email, password, role });
    if (!validation.success) {
      onError(validation.error.issues[0]?.message || "Invalid inputs");
      return;
    }

    setLoading(true);

    try {
      setLoadingStatus("verifying identity…");
      await new Promise((r) => setTimeout(r, 600));
      setLoadingStatus("resolving credentials…");
      await new Promise((r) => setTimeout(r, 600));
      setLoadingStatus("loading AURA…");
      await new Promise((r) => setTimeout(r, 500));

      const res = await login({ email, password, role });

      if (res.success && res.session && res.profile) {
        onSuccess(res.session, res.profile);
      } else {
        onError(res.error || "Authentication failed.");
      }
    } catch (err) {
      console.error("Login submission error:", err);
      onError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
      setLoadingStatus("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label className="text-[10px] font-black uppercase tracking-wider text-[var(--color-aura-ink)] dark:text-slate-200 ml-1">
          {role === "student" ? "university email" : "parent email"}
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
            <Mail className="w-4 h-4" />
          </div>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={role === "student" ? "you@dau.ac.in" : "parent@example.com"}
            className={inputBase}
          />
        </div>
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between ml-1">
          <label className="text-[10px] font-black uppercase tracking-wider text-[var(--color-aura-ink)] dark:text-slate-200">
            password
          </label>
          <a
            href="#"
            onClick={(e) => e.preventDefault()}
            className="text-[10px] font-bold text-brand-600 dark:text-brand-300 hover:underline"
          >
            forgot?
          </a>
        </div>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
            <Lock className="w-4 h-4" />
          </div>
          <input
            type={showPassword ? "text" : "password"}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            maxLength={72}
            className={`${inputBase} pr-10`}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-500 hover:text-[var(--color-aura-ink)] dark:hover:text-slate-200"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>

      <button
        type="submit"
        disabled={loading}
        className="group mt-5 w-full py-3.5 px-5 rounded-2xl bg-brand-500 hover:bg-brand-600 text-white font-black text-sm border-2 border-[var(--color-aura-ink)] shadow-sticker transition-all hover:-translate-y-0.5 active:translate-x-1 active:translate-y-1 active:shadow-none disabled:opacity-70 disabled:cursor-not-allowed disabled:active:translate-x-0 disabled:active:translate-y-0 flex items-center justify-center gap-2 tracking-tight cursor-pointer"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{loadingStatus || "authenticating…"}</span>
          </>
        ) : (
          <>
            <span>sign me in</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </>
        )}
      </button>
    </form>
  );
}
