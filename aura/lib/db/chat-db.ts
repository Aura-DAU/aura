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
// This file lives at aura/lib/db/chat-db.ts → DB sits in the same folder
const DB_DIR  = __dirname
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
  await fs.writeFile(DB_PATH, JSON.stringify(store, null, 2), "utf-8")
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
  const store = await readStore()
  // Keep only the most recent MAX_THREADS
  store[email.toLowerCase()] = threads.slice(0, MAX_THREADS)
  await writeStore(store)
}
