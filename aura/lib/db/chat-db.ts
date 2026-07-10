import fs from "fs/promises"
import path from "path"
import { fileURLToPath } from "url"
import type { ChatMessage, ChatThread } from "@/lib/chat-types"

// ─── Types ───────────────────────────────────────────────────────────────────
export interface StoredThread extends ChatThread {
  messages: ChatMessage[]
}

type ChatStore = Record<string, StoredThread[]> // email -> threads

// ─── File path ────────────────────────────────────────────────────────
const __filename = fileURLToPath(import.meta.url)
const __dirname  = path.dirname(__filename)
// For local hosting, store the DB outside the compiled .next build directory
const DB_DIR  = path.join(process.cwd(), "db")
const DB_PATH = path.join(DB_DIR, "chats.json")
const MAX_THREADS = 10

// ─── Read / write ─────────────────────────────────────────────────────────────
async function readStore(): Promise<ChatStore> {
  try {
    const data = await fs.readFile(DB_PATH, "utf-8")
    return JSON.parse(data) as ChatStore
  } catch {
    await fs.mkdir(DB_DIR, { recursive: true })
    await fs.writeFile(DB_PATH, "{}", "utf-8")
    return {}
  }
}

async function writeStore(store: ChatStore): Promise<void> {
  await fs.mkdir(DB_DIR, { recursive: true })
  // Atomic write: write to a .tmp file then rename over the real file.
  // On Linux, rename() within the same filesystem is atomic, so concurrent
  // writes cannot produce a half-written JSON file.
  const tmpPath = `${DB_PATH}.tmp`
  await fs.writeFile(tmpPath, JSON.stringify(store, null, 2), "utf-8")
  await fs.rename(tmpPath, DB_PATH)
}

// ─── Public API ───────────────────────────────────────────────────────────────
export async function getThreadsForUser(email: string): Promise<StoredThread[]> {
  const store = await readStore()
  return (store[email.toLowerCase()] ?? []).slice(0, MAX_THREADS)
}

export async function saveThreadsForUser(
  email: string,
  threads: StoredThread[]
): Promise<void> {
  // Defence-in-depth: strip personal-data content at the server persistence
  // layer even if the client-side redaction in use-aura-chat.ts were bypassed.
  const sanitised = threads.map((t) => ({
    ...t,
    messages: t.messages.map((m) =>
      m.is_personal_data
        ? { ...m, content: "[Personal data — not stored]" }
        : m
    ),
  }))
  const store = await readStore()
  store[email.toLowerCase()] = sanitised.slice(0, MAX_THREADS)
  await writeStore(store)
}
