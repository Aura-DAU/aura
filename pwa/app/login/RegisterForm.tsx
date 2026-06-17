"use client";

import React, { useState } from "react";
import { User, Mail, GraduationCap, BookOpen, Lock, Loader2, Eye, EyeOff, ArrowRight } from "lucide-react";
import { register } from "@/lib/api/auth.action";
import { RegisterSchema } from "@/lib/api/auth.schema";

interface RegisterFormProps {
  role: "student" | "parent";
  onSuccess: (msg: string) => void;
  onError: (msg: string | null) => void;
}

const inputBase =
  "w-full pl-10 pr-4 py-3 text-sm font-medium bg-white dark:bg-slate-950 border-2 border-[var(--color-aura-ink)] dark:border-slate-100 rounded-2xl text-[var(--color-aura-ink)] dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:translate-x-[2px] focus:translate-y-[2px] focus:shadow-none shadow-sticker-sm transition-all";

const selectBase =
  "w-full px-3 py-3 text-sm font-medium bg-white dark:bg-slate-950 border-2 border-[var(--color-aura-ink)] dark:border-slate-100 rounded-2xl text-[var(--color-aura-ink)] dark:text-slate-100 focus:outline-none focus:translate-x-[2px] focus:translate-y-[2px] focus:shadow-none shadow-sticker-sm transition-all";

const labelBase =
  "text-[10px] font-black uppercase tracking-wider text-[var(--color-aura-ink)] dark:text-slate-200 ml-1";

export function RegisterForm({ role, onSuccess, onError }: RegisterFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const [branch, setBranch] = useState("B.Tech (ICT)");
  const [year] = useState("3rd Year");
  const [semester, setSemester] = useState("Semester I");
  const [interests, setInterests] = useState("");

  const [linkedStudentEmail, setLinkedStudentEmail] = useState("");

  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    onError(null);

    const payload = {
      role,
      email,
      password,
      name,
      branch: role === "student" ? branch : undefined,
      year: role === "student" ? year : undefined,
      semester: role === "student" ? semester : undefined,
      interests: role === "student" ? interests : undefined,
      linkedStudentEmail: role === "parent" ? linkedStudentEmail : undefined,
    };

    const validation = RegisterSchema.safeParse(payload);
    if (!validation.success) {
      onError(validation.error.issues[0]?.message || "Invalid registration details");
      return;
    }

    setLoading(true);

    try {
      setLoadingStatus("connecting to registry…");
      await new Promise((r) => setTimeout(r, 600));
      setLoadingStatus("validating roll records…");
      await new Promise((r) => setTimeout(r, 600));
      setLoadingStatus("generating profile…");
      await new Promise((r) => setTimeout(r, 600));

      if (role === "parent" && linkedStudentEmail) {
        setLoadingStatus("linking student record…");
        await new Promise((r) => setTimeout(r, 500));
      }

      const res = await register(payload);

      if (res.success) {
        onSuccess("account created — sign in to launch AURA.");
      } else {
        onError(res.error || "Registration failed.");
      }
    } catch (err) {
      console.error("Registration submission error:", err);
      onError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
      setLoadingStatus("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <label className={labelBase}>
          {role === "student" ? "full name" : "parent full name"}
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
            <User className="w-4 h-4" />
          </div>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={role === "student" ? "e.g. Aarav Patel" : "e.g. Rajesh Patel"}
            maxLength={100}
            className={inputBase}
          />
        </div>
      </div>
      <div className="space-y-1.5">
        <label className={labelBase}>
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

      {role === "parent" && (
        <div className="space-y-1.5">
          <label className={labelBase}>linked student email</label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
              <GraduationCap className="w-4 h-4" />
            </div>
            <input
              type="email"
              required
              value={linkedStudentEmail}
              onChange={(e) => setLinkedStudentEmail(e.target.value)}
              placeholder="student@dau.ac.in"
              className={inputBase}
            />
          </div>
        </div>
      )}

      {role === "student" && (
        <div className="space-y-3 pt-2">
          <div className="flex gap-3">
            <div className="flex-1 space-y-1.5">
              <label className={labelBase}>branch</label>
              <select
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className={selectBase}
              >
                <option value="B.Tech (ICT)">B.Tech (ICT)</option>
                <option value="B.Tech (MnC)">B.Tech (MnC)</option>
                <option value="M.Tech">M.Tech</option>
                <option value="Ph.D.">Ph.D.</option>
              </select>
            </div>

            <div className="flex-1 space-y-1.5">
              <label className={labelBase}>semester</label>
              <select
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                className={selectBase}
              >
                <option value="Semester I">Sem I</option>
                <option value="Semester II">Sem II</option>
                <option value="Semester III">Sem III</option>
                <option value="Semester IV">Sem IV</option>
                <option value="Semester V">Sem V</option>
                <option value="Semester VI">Sem VI</option>
                <option value="Semester VII">Sem VII</option>
                <option value="Semester VIII">Sem VIII</option>
              </select>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className={labelBase}>interests</label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-500">
                <BookOpen className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
                placeholder="AI, robotics, design…"
                maxLength={300}
                className={inputBase}
              />
            </div>
          </div>
        </div>
      )}

      <div className="space-y-1.5">
        <label className={labelBase}>password</label>
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
            <span>{loadingStatus || "registering…"}</span>
          </>
        ) : (
          <>
            <span>create my account</span>
            <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
          </>
        )}
      </button>
    </form>
  );
}
