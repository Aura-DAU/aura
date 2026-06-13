"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Mail,
  Lock,
  Loader2,
  GraduationCap,
  Users,
  Eye,
  EyeOff,
  User,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  Info
} from "lucide-react";
import { ThemeToggle } from "@/app/components/ThemeToggle";

// Structure for local storage mock database
interface StudentProfileData {
  name: string;
  branch: string;
  year: string;
  semester: string;
  interests: string;
}

interface UserAccount {
  role: "student" | "parent";
  email: string;
  password: string;
  name: string;
  // Student specific
  branch?: string;
  year?: string;
  semester?: string;
  interests?: string;
  // Parent specific
  linkedStudentEmail?: string;
}

const DEFAULT_USERS: UserAccount[] = [
  {
    role: "student",
    email: "student@dau.edu",
    password: "password123",
    name: "Aarav Patel",
    branch: "B.Tech (ICT)",
    year: "3rd Year",
    semester: "Semester V",
    interests: "Artificial Intelligence, competitive coding"
  },
  {
    role: "parent",
    email: "parent@example.com",
    password: "password123",
    name: "Rajesh Patel",
    linkedStudentEmail: "student@dau.edu"
  }
];

export default function LoginPage() {
  const router = useRouter();

  // Auth Modes: "signin" or "signup"
  const [authMode, setAuthMode] = useState<"signin" | "signup">("signin");
  // Roles: "student" or "parent"
  const [role, setRole] = useState<"student" | "parent">("student");

  // Input states
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Student specific inputs (Sign Up)
  const [branch, setBranch] = useState("B.Tech (ICT)");
  const [year, setYear] = useState("3rd Year");
  const [semester, setSemester] = useState("Semester V");
  const [interests, setInterests] = useState("");

  // Parent specific inputs
  const [linkedStudentEmail, setLinkedStudentEmail] = useState("");

  // Feedback states
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState("");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Initialize mock users in localStorage on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const existing = localStorage.getItem("aura_users");
      if (!existing) {
        localStorage.setItem("aura_users", JSON.stringify(DEFAULT_USERS));
      }
    }
  }, []);

  // Clear inputs when toggling modes
  useEffect(() => {
    setEmail("");
    setPassword("");
    setName("");
    setInterests("");
    setLinkedStudentEmail("");
    setErrorMsg(null);
    setSuccessMsg(null);
  }, [authMode, role]);

  const handleFillDemo = (demoType: "student" | "parent") => {
    setErrorMsg(null);
    setAuthMode("signin");
    if (demoType === "student") {
      setRole("student");
      setEmail("student@dau.edu");
      setPassword("password123");
    } else {
      setRole("parent");
      setEmail("parent@example.com");
      setPassword("password123");
    }
  };

  const validateForm = (): boolean => {
    if (!email || !password) {
      setErrorMsg("Email and password are required.");
      return false;
    }

    if (password.length < 6) {
      setErrorMsg("Password must be at least 6 characters.");
      return false;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setErrorMsg("Please enter a valid email address.");
      return false;
    }

    if (role === "student" && email.endsWith("@dau.edu") === false && authMode === "signup") {
      setErrorMsg("Student registration requires a university domain email (@dau.edu).");
      return false;
    }

    if (authMode === "signup") {
      if (!name) {
        setErrorMsg("Full name is required.");
        return false;
      }
      if (role === "parent" && !linkedStudentEmail) {
        setErrorMsg("Linked Student Email is required.");
        return false;
      }
    }

    setErrorMsg(null);
    return true;
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;

    setLoading(true);

    // Load registered users from localStorage
    const savedUsersStr = localStorage.getItem("aura_users") || JSON.stringify(DEFAULT_USERS);
    const users: UserAccount[] = JSON.parse(savedUsersStr);

    if (authMode === "signup") {
      // Check if user already exists
      const userExists = users.some((u) => u.email.toLowerCase() === email.toLowerCase());
      if (userExists) {
        setLoading(false);
        setErrorMsg("An account with this email already exists.");
        return;
      }

      // Simulate registration milestones
      setLoadingStatus("Connecting to University registry database...");
      await new Promise((r) => setTimeout(r, 600));

      setLoadingStatus("Validating student roll records...");
      await new Promise((r) => setTimeout(r, 600));

      setLoadingStatus("Generating credential profiles...");
      await new Promise((r) => setTimeout(r, 600));

      // Build new user account
      const newUser: UserAccount = {
        role,
        email,
        password,
        name,
        branch: role === "student" ? branch : undefined,
        year: role === "student" ? year : undefined,
        semester: role === "student" ? semester : undefined,
        interests: role === "student" ? (interests || "General academic interest") : undefined,
        linkedStudentEmail: role === "parent" ? linkedStudentEmail : undefined
      };

      // If parent, check if student exists
      if (role === "parent") {
        const studentExists = users.some(
          (u) => u.role === "student" && u.email.toLowerCase() === linkedStudentEmail.toLowerCase()
        );
        if (!studentExists) {
          // Provide friendly warning but allow it, mapping to standard student if not found in db
          setLoadingStatus("Warning: Student record not found. Linking with default profile anyway...");
          await new Promise((r) => setTimeout(r, 800));
        }
      }

      // Save to mock database
      users.push(newUser);
      localStorage.setItem("aura_users", JSON.stringify(users));

      setLoading(false);
      setSuccessMsg("Account successfully registered! You can now sign in.");
      setAuthMode("signin");
    } else {
      // SIGN IN FLOW
      setLoadingStatus("Verifying identity via LDAP server...");
      await new Promise((r) => setTimeout(r, 600));

      setLoadingStatus("Resolving academic credentials...");
      await new Promise((r) => setTimeout(r, 600));

      // Find user
      const user = users.find(
        (u) =>
          u.email.toLowerCase() === email.toLowerCase() &&
          u.password === password &&
          u.role === role
      );

      if (!user) {
        setLoading(false);
        setErrorMsg("Invalid email, password, or role selection.");
        return;
      }

      setLoadingStatus("Injecting context and loading AURA desktop...");
      await new Promise((r) => setTimeout(r, 500));

      // Save session info
      const sessionData = {
        role: user.role,
        email: user.email,
        name: user.name,
        linkedStudentEmail: user.linkedStudentEmail
      };
      localStorage.setItem("aura_session", JSON.stringify(sessionData));

      // Sync student profile so AURA knows details
      let profileToSet: StudentProfileData;

      if (user.role === "student") {
        profileToSet = {
          name: user.name,
          branch: user.branch || "B.Tech (ICT)",
          year: user.year || "3rd Year",
          semester: user.semester || "Semester V",
          interests: user.interests || "Artificial Intelligence, competitive coding"
        };
      } else {
        // Parent: find the linked student
        const linkedStudent = users.find(
          (u) =>
            u.role === "student" &&
            u.email.toLowerCase() === (user.linkedStudentEmail || "").toLowerCase()
        );

        profileToSet = {
          name: linkedStudent ? linkedStudent.name : "Aarav Patel",
          branch: linkedStudent ? (linkedStudent.branch || "B.Tech (ICT)") : "B.Tech (ICT)",
          year: linkedStudent ? (linkedStudent.year || "3rd Year") : "3rd Year",
          semester: linkedStudent ? (linkedStudent.semester || "Semester V") : "Semester V",
          interests: linkedStudent
            ? (linkedStudent.interests || "Artificial Intelligence, competitive coding")
            : "Artificial Intelligence, competitive coding"
        };
      }

      localStorage.setItem("aura_student_profile", JSON.stringify(profileToSet));

      setLoading(false);
      router.push("/");
    }
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

            {/* Main Form */}
            <form onSubmit={handleAuthSubmit} className="space-y-4">
              
              {/* Name Field (Sign Up Only) */}
              {authMode === "signup" && (
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
              )}

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

              {/* Linked Student ID/Email (Parent Sign Up / Parent Sign In) */}
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
                      required={authMode === "signup"}
                      value={linkedStudentEmail}
                      onChange={(e) => setLinkedStudentEmail(e.target.value)}
                      placeholder="e.g. student@dau.edu"
                      className="w-full pl-10 pr-4 py-2.5 text-sm bg-white/50 dark:bg-slate-950/50 border border-slate-200 dark:border-slate-800 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand-500/50 focus:border-brand-500 text-slate-900 dark:text-slate-100 placeholder-slate-400 transition-all"
                    />
                  </div>
                  {authMode === "signin" && (
                    <span className="text-[10px] text-slate-400 dark:text-slate-500 block ml-1 leading-snug">
                      Optional: Leave blank to use default child profile linkage.
                    </span>
                  )}
                </div>
              )}

              {/* Student Academic Details (Sign Up Only) */}
              {authMode === "signup" && role === "student" && (
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
                <div className="flex items-center justify-between ml-1">
                  <label className="text-xs font-medium text-slate-700 dark:text-slate-300">
                    Password
                  </label>
                  {authMode === "signin" && (
                    <a href="#" className="text-[10px] font-medium text-brand-600 dark:text-brand-400 hover:underline">
                      Forgot password?
                    </a>
                  )}
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
                  <span>{authMode === "signin" ? "Sign In" : "Register Profile"}</span>
                )}
              </button>
            </form>

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
          <div className="mt-6 p-4 bg-white/40 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800/60 rounded-2xl shadow-sm">
            <div className="flex items-center gap-2 mb-2 text-xs font-semibold text-slate-700 dark:text-slate-300">
              <Info className="w-3.5 h-3.5 text-brand-500 shrink-0" />
              <span>Demo Quick-Fill Credentials</span>
            </div>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 mb-3 leading-relaxed">
              Use these buttons to instantly log in using preset Student or Parent profiles for testing.
            </p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => handleFillDemo("student")}
                className="flex-1 py-2 px-3 text-[11px] font-semibold border border-brand-200 dark:border-brand-900/50 hover:bg-brand-50 dark:hover:bg-brand-950/20 text-brand-700 dark:text-brand-400 bg-white/70 dark:bg-slate-900/70 rounded-xl transition-colors cursor-pointer"
              >
                Demo Student Account
              </button>
              <button
                type="button"
                onClick={() => handleFillDemo("parent")}
                className="flex-1 py-2 px-3 text-[11px] font-semibold border border-brand-200 dark:border-brand-900/50 hover:bg-brand-50 dark:hover:bg-brand-950/20 text-brand-700 dark:text-brand-400 bg-white/70 dark:bg-slate-900/70 rounded-xl transition-colors cursor-pointer"
              >
                Demo Parent Account
              </button>
            </div>
          </div>

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
