import fs from "fs/promises"
import path from "path"
import { fileURLToPath } from "url"
import crypto from "crypto"

// ─── Types ───────────────────────────────────────────────────────────────────
export interface UserAccount {
  role: "student" | "parent" | "faculty"
  email: string
  name: string
  passwordHash: string
  createdAt: string
  linkedStudentEmail?: string // parent only
  department?: string // faculty only
}

// ─── PBKDF2 password hashing (no external deps) ──────────────────────────────
const ITERATIONS = 100_000
const KEY_LEN    = 64
const DIGEST     = "sha512"

export function hashPassword(password: string): string {
  const salt = crypto.randomBytes(16).toString("hex")
  const hash = crypto
    .pbkdf2Sync(password, salt, ITERATIONS, KEY_LEN, DIGEST)
    .toString("hex")
  return `${salt}:${hash}`
}

export function verifyPassword(password: string, stored: string): boolean {
  const [salt, hash] = stored.split(":")
  if (!salt || !hash) return false
  const candidate = crypto
    .pbkdf2Sync(password, salt, ITERATIONS, KEY_LEN, DIGEST)
    .toString("hex")
  try {
    return crypto.timingSafeEqual(
      Buffer.from(candidate, "hex"),
      Buffer.from(hash, "hex")
    )
  } catch {
    return false
  }
}

// ─── File paths ────────────────────────────────────────────────────────
const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)
// For local hosting, store the DB outside the compiled .next build directory
const DB_DIR  = path.join(process.cwd(), "db")
const DB_PATH = path.join(DB_DIR, "users.json")

// ─── Read / write ─────────────────────────────────────────────────────────────
export async function getUsers(): Promise<UserAccount[]> {
  try {
    const data = await fs.readFile(DB_PATH, "utf-8")
    return JSON.parse(data) as UserAccount[]
  } catch {
    await fs.mkdir(DB_DIR, { recursive: true })
    await fs.writeFile(DB_PATH, "[]", "utf-8")
    return []
  }
}

async function writeUsers(users: UserAccount[]): Promise<void> {
  await fs.mkdir(DB_DIR, { recursive: true })
  await fs.writeFile(DB_PATH, JSON.stringify(users, null, 2), "utf-8")
}

// ─── Public API ───────────────────────────────────────────────────────────────
export async function findUser(
  email: string,
  role: "student" | "parent" | "faculty"
): Promise<UserAccount | undefined> {
  const users = await getUsers()
  const found = users.find(
    (u) => u.email.toLowerCase() === email.toLowerCase() && u.role === role
  )
  if (found) return found

  // Auto-support demo credentials
  if (role === "student" && email.toLowerCase() === "demo.student@dau.ac.in") {
    return {
      role: "student",
      email: "demo.student@dau.ac.in",
      name: "Demo Student",
      passwordHash: hashPassword("Student@123"),
      createdAt: new Date().toISOString()
    }
  }
  if (role === "parent" && email.toLowerCase() === "parent.demo@gmail.com") {
    return {
      role: "parent",
      email: "parent.demo@gmail.com",
      name: "Demo Parent",
      passwordHash: hashPassword("Parent@123"),
      createdAt: new Date().toISOString()
    }
  }
  if (role === "faculty" && email.toLowerCase() === "demo.faculty@daiict.ac.in") {
    return {
      role: "faculty",
      email: "demo.faculty@daiict.ac.in",
      name: "Demo Faculty",
      department: "Information & Communication Technology",
      passwordHash: hashPassword("Faculty@123"),
      createdAt: new Date().toISOString()
    }
  }

  return undefined
}

export async function saveUser(
  user: Omit<UserAccount, "passwordHash" | "createdAt"> & { password: string }
): Promise<UserAccount> {
  const users = await getUsers()
  const isDemo =
    (user.role === "student" && user.email.toLowerCase() === "demo.student@dau.ac.in") ||
    (user.role === "parent" && user.email.toLowerCase() === "parent.demo@gmail.com") ||
    (user.role === "faculty" && user.email.toLowerCase() === "demo.faculty@daiict.ac.in")
  const exists = users.some(
    (u) => u.email.toLowerCase() === user.email.toLowerCase() && u.role === user.role
  )
  if (exists || isDemo) throw new Error("USER_EXISTS")

  const { password, ...rest } = user
  const record: UserAccount = {
    ...rest,
    passwordHash: hashPassword(password),
    createdAt: new Date().toISOString(),
  }
  users.push(record)
  await writeUsers(users)
  return record
}
