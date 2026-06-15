import fs from "fs/promises";
import path from "path";
import crypto from "crypto";

export interface UserAccount {
  role: "student" | "parent";
  email: string;
  // FIX: stored as PBKDF2 hash — never plaintext
  passwordHash: string;
  name: string;
  branch?: string;
  year?: string;
  semester?: string;
  interests?: string;
  linkedStudentEmail?: string;
}

// ---------- Password hashing (PBKDF2, no external deps) ----------
const ITERATIONS = 100_000;
const KEY_LEN = 64;
const DIGEST = "sha512";

export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString("hex");
  const hash = crypto
    .pbkdf2Sync(password, salt, ITERATIONS, KEY_LEN, DIGEST)
    .toString("hex");
  return `${salt}:${hash}`;
}

export function verifyPassword(password: string, stored: string): boolean {
  const [salt, hash] = stored.split(":");
  if (!salt || !hash) return false;
  const candidate = crypto
    .pbkdf2Sync(password, salt, ITERATIONS, KEY_LEN, DIGEST)
    .toString("hex");
  // Constant-time comparison — prevents timing oracle
  return crypto.timingSafeEqual(Buffer.from(candidate, "hex"), Buffer.from(hash, "hex"));
}

// ---------- Default seed users (hashed) ----------
// FIX: Passwords are now hashed at startup — no more plaintext in source
const _RAW_DEFAULTS = [
  {
    role: "student" as const,
    email: "student@dau.edu",
    password: "password123",
    name: "Aarav Patel",
    branch: "B.Tech (ICT)",
    year: "3rd Year",
    semester: "Semester V",
    interests: "Artificial Intelligence, competitive coding",
  },
  {
    role: "parent" as const,
    email: "parent@example.com",
    password: "password123",
    name: "Rajesh Patel",
    linkedStudentEmail: "student@dau.edu",
  },
];

export const DEFAULT_USERS: UserAccount[] = _RAW_DEFAULTS.map(({ password, ...rest }) => ({
  ...rest,
  passwordHash: hashPassword(password),
}));

// ---------- File-based DB ----------
const DB_DIR = path.join(process.cwd(), "lib/db");
const DB_PATH = path.join(DB_DIR, "users.json");

export async function getUsers(): Promise<UserAccount[]> {
  try {
    const data = await fs.readFile(DB_PATH, "utf-8");
    return JSON.parse(data);
  } catch {
    try {
      await fs.mkdir(DB_DIR, { recursive: true });
      await fs.writeFile(DB_PATH, JSON.stringify(DEFAULT_USERS, null, 2), "utf-8");
    } catch (err) {
      console.error("Failed to initialize default users file:", err);
    }
    return DEFAULT_USERS;
  }
}

export async function saveUser(
  user: Omit<UserAccount, "passwordHash"> & { password: string }
): Promise<void> {
  const users = await getUsers();
  if (users.some((u) => u.email.toLowerCase() === user.email.toLowerCase())) {
    throw new Error("User already exists");
  }
  const { password, ...rest } = user;
  const newRecord: UserAccount = { ...rest, passwordHash: hashPassword(password) };
  users.push(newRecord);
  await fs.mkdir(DB_DIR, { recursive: true });
  await fs.writeFile(DB_PATH, JSON.stringify(users, null, 2), "utf-8");
}

export async function updateUserProfile(
  email: string,
  role: "student" | "parent",
  profile: { name: string; branch: string; semester: string; interests: string }
): Promise<void> {
  const users = await getUsers();
  const index = users.findIndex(
    (u) => u.email.toLowerCase() === email.toLowerCase() && u.role === role
  );
  if (index === -1) throw new Error("User not found");

  users[index].name = profile.name;
  if (users[index].role === "student") {
    users[index].branch = profile.branch;
    users[index].semester = profile.semester;
    users[index].interests = profile.interests;
  }

  await fs.mkdir(DB_DIR, { recursive: true });
  await fs.writeFile(DB_PATH, JSON.stringify(users, null, 2), "utf-8");
}