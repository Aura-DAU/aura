"use client";

import React, { useState } from "react";
import { User, Mail, GraduationCap, BookOpen, Lock, Loader2, Eye, EyeOff } from "lucide-react";
import { register } from "@/lib/api/auth.action";
import { RegisterSchema } from "@/lib/api/auth.schema";

interface RegisterFormProps {
  role: "student" | "parent";
  onSuccess: (msg: string) => void;
  onError: (msg: string | null) => void;
}

export function RegisterForm({ role, onSuccess, onError }: RegisterFormProps) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Student specific inputs
  const [branch, setBranch] = useState("B.Tech (ICT)");
  const [year] = useState("3rd Year");
  const [semester, setSemester] = useState("Semester V");
  const [interests, setInterests] = useState("");

  // Parent specific inputs
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

    // Client-side Zod validation with refinements
    const validation = RegisterSchema.safeParse(payload);
    if (!validation.success) {
      onError(validation.error.issues[0]?.message || "Invalid registration details");
      return;
    }

    setLoading(true);

    try {
      // Simulate registration milestones
      setLoadingStatus("Connecting to University registry database...");
      await new Promise((r) => setTimeout(r, 600));

      setLoadingStatus("Validating student roll records...");
      await new Promise((r) => setTimeout(r, 600));

      setLoadingStatus("Generating credential profiles...");
      await new Promise((r) => setTimeout(r, 600));

      if (role === "parent" && linkedStudentEmail) {
        setLoadingStatus("Verifying linked student record database...");
        await new Promise((r) => setTimeout(r, 500));
      }

      const res = await register(payload);

      if (res.success) {
        onSuccess("Account successfully registered! You can now sign in.");
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
      {/* Name Field */}
      <div className="space-y-1">
        <label className="text-xs font-medium text-slate-700 dark:text-slate-300 ml-1">
          {role === "student" ? "Full Student Name" : "Parent Full Name"}
        </label>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
            <User className="w-4 h-4" />
          </div>
          <input
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder={role === "student" ? "e.g. Aarav Patel" : "e.g. Rajesh Patel"}
            className="w-full pl-10 pr-4 py-2.5 text-sm bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-all"
          />
        </div>
      </div>

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

      {/* Linked Student ID/Email (Parent Only) */}
      {role === "parent" && (
        <div className="space-y-1">
          <label className="text-xs font-medium text-slate-700 dark:text-slate-300 ml-1">
            Linked Student Email ID
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
              <GraduationCap className="w-4 h-4" />
            </div>
            <input
              type="email"
              required
              value={linkedStudentEmail}
              onChange={(e) => setLinkedStudentEmail(e.target.value)}
              placeholder="e.g. student@dau.edu"
              className="w-full pl-10 pr-4 py-2.5 text-sm bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-all"
            />
          </div>
        </div>
      )}

      {/* Student Academic Details (Student Only) */}
      {role === "student" && (
        <div className="space-y-3 pt-1 border-t border-slate-100 dark:border-slate-800/60 mt-3">
          <div className="flex gap-3">
            <div className="flex-1 space-y-1">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300 ml-1">Branch</label>
              <select
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 transition-all"
              >
                <option value="B.Tech (ICT)">B.Tech (ICT)</option>
                <option value="B.Tech (MnC)">B.Tech (MnC)</option>
                <option value="M.Tech">M.Tech</option>
                <option value="Ph.D.">Ph.D.</option>
              </select>
            </div>

            <div className="flex-1 space-y-1">
              <label className="text-xs font-medium text-slate-700 dark:text-slate-300 ml-1">Semester</label>
              <select
                value={semester}
                onChange={(e) => setSemester(e.target.value)}
                className="w-full px-3 py-2 text-xs bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 transition-all"
              >
                <option value="Semester I">Sem I</option>
                <option value="Semester III">Sem III</option>
                <option value="Semester V">Sem V</option>
                <option value="Semester VII">Sem VII</option>
              </select>
            </div>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-slate-700 dark:text-slate-300 ml-1">
              Interests / Research Areas
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 dark:text-slate-500">
                <BookOpen className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={interests}
                onChange={(e) => setInterests(e.target.value)}
                placeholder="e.g. AI, Cyber Security, Robotics"
                className="w-full pl-10 pr-4 py-2.5 text-sm bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-all"
              />
            </div>
          </div>
        </div>
      )}

      {/* Password */}
      <div className="space-y-1">
        <label className="text-xs font-medium text-slate-700 dark:text-slate-300 ml-1">
          Password
        </label>
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
            <span>{loadingStatus || "Registering..."}</span>
          </>
        ) : (
          <span>Register Profile</span>
        )}
      </button>
    </form>
  );
}
