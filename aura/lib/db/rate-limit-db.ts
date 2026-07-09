import fs from "fs/promises"
import path from "path"

export interface RateLimitEntry {
  count: number
  date: string
}

type RateLimitStore = Record<string, RateLimitEntry>

const DB_DIR = path.join(process.cwd(), "db")
const DB_PATH = path.join(DB_DIR, "rate_limits.json")

async function readStore(): Promise<RateLimitStore> {
  try {
    const data = await fs.readFile(DB_PATH, "utf-8")
    return JSON.parse(data) as RateLimitStore
  } catch {
    await fs.mkdir(DB_DIR, { recursive: true })
    await fs.writeFile(DB_PATH, "{}", "utf-8")
    return {}
  }
}

async function writeStore(store: RateLimitStore): Promise<void> {
  await fs.mkdir(DB_DIR, { recursive: true })
  const tmpPath = `${DB_PATH}.tmp`
  await fs.writeFile(tmpPath, JSON.stringify(store, null, 2), "utf-8")
  await fs.rename(tmpPath, DB_PATH)
}

function getTodayString(): string {
  return new Date().toISOString().split("T")[0]
}

export function getMaxQuota(role: string): number {
  return role === "guest" ? 3 : 5
}

export async function getRemainingQuota(sub: string, role: string): Promise<number> {
  const store = await readStore()
  const entry = store[sub]
  const today = getTodayString()
  const maxQuota = getMaxQuota(role)

  if (!entry || entry.date !== today) {
    return maxQuota
  }
  return Math.max(0, maxQuota - entry.count)
}

export async function incrementQuotaUsage(sub: string, role: string): Promise<number> {
  const store = await readStore()
  const today = getTodayString()
  const maxQuota = getMaxQuota(role)
  const entry = store[sub]

  if (!entry || entry.date !== today) {
    store[sub] = { count: 1, date: today }
  } else {
    store[sub] = { count: entry.count + 1, date: today }
  }

  await writeStore(store)
  return Math.max(0, maxQuota - store[sub].count)
}

export async function pruneOldEntries(maxDays = 7): Promise<void> {
  const store = await readStore()
  const today = new Date()
  let modified = false

  for (const [sub, entry] of Object.entries(store)) {
    try {
      const entryDate = new Date(entry.date)
      const diffTime = Math.abs(today.getTime() - entryDate.getTime())
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))
      if (diffDays > maxDays) {
        delete store[sub]
        modified = true
      }
    } catch {
      delete store[sub]
      modified = true
    }
  }

  if (modified) {
    await writeStore(store)
  }
}
