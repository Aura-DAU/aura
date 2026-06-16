"use client";

import React, { useState } from "react";
import { Mail, Lock, Loader2, Eye, EyeOff } from "lucide-react";
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

    // Client-side Zod Validation
    const validation = LoginSchema.safeParse({ email, password, role });
    if (!validation.success) {
      onError(validation.error.issues[0]?.message || "Invalid inputs");
      return;
    }

    setLoading(true);

    try {
      // Simulate authenticating milestones
      setLoadingStatus("Verifying identity via LDAP server...");
      await new Promise((r) => setTimeout(r, 600));

      setLoadingStatus("Resolving academic credentials...");
      await new Promise((r) => setTimeout(r, 600));

      setLoadingStatus("Injecting context and loading AURA desktop...");
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
      {/* Email Address */}
      <div className="space-y-1">
        <label className="text-xs font-medium text-slate-700 dark:text-slate-300 ml-1">
          {role === "student" ? "University Email ID" : "Parent Email Address"}
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
            <Mail className="w-4 h-4" />
          </div>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder={role === "student" ? "student@dau.edu" : "parent@example.com"}
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-all"
          />
        </div>
      </div>

      {/* Password */}
      <div className="space-y-1">
        <div className="flex items-center justify-between ml-1">
          <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
            Password
          </label>
          <a
            href="#"
            onClick={(e) => e.preventDefault()}
            className="text-[10px] font-medium text-brand-600 dark:text-brand-400 hover:underline"
          >
            Forgot password?
          </a>
        </div>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
            <Lock className="w-4 h-4" />
          </div>
          <input
            type={showPassword ? "text" : "password"}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full pl-10 pr-10 py-2.5 text-sm bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-all"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 px-4 bg-brand-600 hover:bg-brand-700 text-white font-medium text-sm rounded-xl shadow-lg shadow-brand-500/20 dark:shadow-brand-500/10 transition-all hover:shadow-brand-500/30 active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed disabled:active:scale-100 flex items-center justify-center gap-2 mt-6 cursor-pointer"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>{loadingStatus || "Authenticating..."}</span>
          </>
        ) : (
          <span>Sign In</span>
        )}
      </button>
    </form>
  );
}
