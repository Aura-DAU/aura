"use server";

import { cookies, headers } from "next/headers";
import { getUsers, saveUser, updateUserProfile, UserAccount } from "@/lib/db/user-db";
import { Redis } from "@upstash/redis";
import { Ratelimit } from "@upstash/ratelimit";

// Import schemas and types from your new file
import { 
  LoginSchema, 
  RegisterSchema, 
  LoginInput, 
  RegisterInput, 
  UserSession 
} from "./auth.schema";

// Initialize Redis & Ratelimit
const redis = new Redis({
  url: process.env.UPSTASH_REDIS_REST_URL!,
  token: process.env.UPSTASH_REDIS_REST_TOKEN!,
});

const ratelimit = new Ratelimit({
  redis: redis,
  limiter: Ratelimit.slidingWindow(5, "60 s"), // 5 attempts per minute
});

export async function login(input: LoginInput) {
  const headersList = await headers();
  const ip = headersList.get("x-forwarded-for") || "127.0.0.1";
  
  const { success } = await ratelimit.limit(ip);
  if (!success) {
    return { success: false, error: "Too many login attempts. Please try again in a minute." };
  }

  // Validate input schema
  const parsed = LoginSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: parsed.error.issues[0]?.message || "Invalid input data",
    };
  }

  const { email, password, role } = parsed.data;
  const users = await getUsers();
  const user = users.find(
    (u) =>
      u.email.toLowerCase() === email.toLowerCase() &&
      u.password === password &&
      u.role === role
  );

  if (!user) {
    return {
      success: false,
      error: "Invalid email, password, or role selection.",
    };
  }

  const sessionData: UserSession = {
    role: user.role,
    email: user.email,
    name: user.name,
    linkedStudentEmail: user.linkedStudentEmail,
  };

  // Set next/headers httpOnly cookie session
  const cookieStore = await cookies();
  cookieStore.set("aura_session", JSON.stringify(sessionData), {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 60 * 60 * 24 * 7, // 1 week
    path: "/",
  });

  // Calculate profile to return to frontend
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
      name: linkedStudent ? linkedStudent.name : "Aarav Patel",
      branch: linkedStudent ? (linkedStudent.branch || "B.Tech (ICT)") : "B.Tech (ICT)",
      year: linkedStudent ? (linkedStudent.year || "3rd Year") : "3rd Year",
      semester: linkedStudent ? (linkedStudent.semester || "Semester V") : "Semester V",
      interests: linkedStudent
        ? (linkedStudent.interests || "Artificial Intelligence, competitive coding")
        : "Artificial Intelligence, competitive coding",
    };
  }

  return {
    success: true,
    session: sessionData,
    profile: profileToSet,
  };
}

export async function register(input: RegisterInput) {
  // Validate input schema with role refinements
  const parsed = RegisterSchema.safeParse(input);
  if (!parsed.success) {
    return {
      success: false,
      error: parsed.error.issues[0]?.message || "Invalid input data",
    };
  }

  const { role, email, password, name, branch, year, semester, interests, linkedStudentEmail } = parsed.data;
  const users = await getUsers();

  if (users.some((u) => u.email.toLowerCase() === email.toLowerCase())) {
    return {
      success: false,
      error: "An account with this email already exists.",
    };
  }

  const newUser: UserAccount = {
    role,
    email,
    password,
    name,
    branch: role === "student" ? branch : undefined,
    year: role === "student" ? year : undefined,
    semester: role === "student" ? semester : undefined,
    interests: role === "student" ? (interests || "General academic interest") : undefined,
    linkedStudentEmail: role === "parent" ? linkedStudentEmail : undefined,
  };

  try {
    await saveUser(newUser);
  } catch (err) {
    const errorMsg = err instanceof Error ? err.message : "Failed to save user account";
    return {
      success: false,
      error: errorMsg,
    };
  }

  return {
    success: true,
  };
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
    const errorMsg = err instanceof Error ? err.message : "Failed to update profile";
    return { success: false, error: errorMsg };
  }
}
