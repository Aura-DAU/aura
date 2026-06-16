"use server";

import { cookies, headers } from "next/headers";
import { getUsers, saveUser, updateUserProfile, verifyPassword } from "@/lib/db/user-db";
import { LoginSchema, RegisterSchema, LoginInput, RegisterInput } from "./auth.schema";

export interface UserSession {
  role: "student" | "parent";
  email: string;
  name: string;
  linkedStudentEmail?: string;
}

// TODO: Move in-process rate limiting to a shared store (Redis/Upstash) before deploying.
interface RateBucket {
  count: number;
  firstFail: number;
  lockedUntil: number;
}
const loginAttempts = new Map<string, RateBucket>();
const MAX_ATTEMPTS = 5;
const WINDOW_MS = 15 * 60 * 1000;   // 15 min rolling window
const LOCKOUT_MS = 15 * 60 * 1000;  // 15 min lockout after MAX_ATTEMPTS

function checkRateLimit(key: string): { allowed: boolean; retryAfterSec?: number } {
  const now = Date.now();
  const bucket = loginAttempts.get(key);

  if (!bucket) return { allowed: true };

  // Still in lockout?
  if (bucket.lockedUntil > now) {
    return { allowed: false, retryAfterSec: Math.ceil((bucket.lockedUntil - now) / 1000) };
  }

  // Window expired — reset
  if (now - bucket.firstFail > WINDOW_MS) {
    loginAttempts.delete(key);
    return { allowed: true };
  }

  return { allowed: true };
}

function recordFailedAttempt(key: string): void {
  const now = Date.now();
  const bucket = loginAttempts.get(key);

  if (!bucket || now - bucket.firstFail > WINDOW_MS) {
    loginAttempts.set(key, { count: 1, firstFail: now, lockedUntil: 0 });
    return;
  }

  bucket.count += 1;
  if (bucket.count >= MAX_ATTEMPTS) {
    bucket.lockedUntil = now + LOCKOUT_MS;
  }
  loginAttempts.set(key, bucket);
}

function clearAttempts(key: string): void {
  loginAttempts.delete(key);
}

// ─────────────────────────────────────────────────────────────────────────────

export async function login(input: LoginInput) {
  const parsed = LoginSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0]?.message || "Invalid input data" };
  }

  const { email, password, role } = parsed.data;

  const headersList = await headers();
  const ip = headersList.get("x-forwarded-for")?.split(",")[0].trim() || "unknown";
  const rlKey = `login:${ip}:${email.toLowerCase()}`;
  const rl = checkRateLimit(rlKey);
  if (!rl.allowed) {
    return {
      success: false,
      error: `Too many failed attempts. Try again in ${rl.retryAfterSec} seconds.`,
    };
  }

  const users = await getUsers();
  const user = users.find(
    (u) =>
      u.email.toLowerCase() === email.toLowerCase() &&
      u.role === role
  );

  // Always call verifyPassword even if user not found (dummy hash) to
  // avoid timing-based user-enumeration.
  const DUMMY_HASH = "00000000000000000000000000000000:0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000";
  const storedHash = user?.passwordHash ?? DUMMY_HASH;
  const passwordOk = verifyPassword(password, storedHash);

  if (!user || !passwordOk) {
    recordFailedAttempt(rlKey);
    return { success: false, error: "Invalid email, password, or role selection." };
  }

  clearAttempts(rlKey);

  const sessionData: UserSession = {
    role: user.role,
    email: user.email,
    name: user.name,
    linkedStudentEmail: user.linkedStudentEmail,
  };

  const cookieStore = await cookies();
  cookieStore.set("aura_session", JSON.stringify(sessionData), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7,
    path: "/",
  });

  let profileToSet;
  if (user.role === "student") {
    profileToSet = {
      name: user.name,
      branch: user.branch || "B.Tech (ICT)",
      year: user.year || "3rd Year",
      semester: user.semester || "Semester V",
      interests: user.interests || "Artificial Intelligence, competitive coding",
    };
  } else {
    const linkedStudent = users.find(
      (u) =>
        u.role === "student" &&
        u.email.toLowerCase() === (user.linkedStudentEmail || "").toLowerCase()
    );
    profileToSet = {
      name: linkedStudent?.name ?? "Aarav Patel",
      branch: linkedStudent?.branch ?? "B.Tech (ICT)",
      year: linkedStudent?.year ?? "3rd Year",
      semester: linkedStudent?.semester ?? "Semester V",
      interests: linkedStudent?.interests ?? "Artificial Intelligence, competitive coding",
    };
  }

  return { success: true, session: sessionData, profile: profileToSet };
}

export async function register(input: RegisterInput) {
  const parsed = RegisterSchema.safeParse(input);
  if (!parsed.success) {
    return { success: false, error: parsed.error.issues[0]?.message || "Invalid input data" };
  }

  const { role, email, password, name, branch, year, semester, interests, linkedStudentEmail } =
    parsed.data;
  const users = await getUsers();

  if (users.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
    return { success: false, error: "An account with this email already exists." };
  }

  try {
    // saveUser now hashes the password internally before persisting
    await saveUser({
      role,
      email,
      password,  // raw — hashed inside saveUser
      name,
      branch: role === "student" ? branch : undefined,
      year: role === "student" ? year : undefined,
      semester: role === "student" ? semester : undefined,
      interests: role === "student" ? (interests || "General academic interest") : undefined,
      linkedStudentEmail: role === "parent" ? linkedStudentEmail : undefined,
    });
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Failed to save user account" };
  }

  return { success: true };
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete("aura_session");
  return { success: true };
}

export async function getSession(): Promise<UserSession | null> {
  const cookieStore = await cookies();
  const sessionCookie = cookieStore.get("aura_session");
  if (!sessionCookie) return null;
  try {
    return JSON.parse(sessionCookie.value) as UserSession;
  } catch {
    return null;
  }
}

export async function updateProfile(
  email: string,
  role: "student" | "parent",
  profile: { name: string; branch: string; semester: string; interests: string }
) {
  try {
    await updateUserProfile(email, role, profile);
    return { success: true };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : "Failed to update profile" };
  }
}