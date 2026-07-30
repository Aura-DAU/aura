import fs from "fs/promises"
import path from "path"
import type { ChatMessage, ChatThread } from "@/lib/chat-types"

// ─── Types ───────────────────────────────────────────────────────────────────
export interface StoredThread extends ChatThread {
  messages: ChatMessage[]
}

type ChatStore = Record<string, StoredThread[]> // email -> threads

interface SyncMetaStore {
  /** email -> last accepted clientSyncAt */
  [email: string]: number
}

// ─── File path ────────────────────────────────────────────────────────
// For local hosting, store the DB outside the compiled .next build directory
const DB_DIR = path.join(process.cwd(), "db")
const DB_PATH = path.join(DB_DIR, "chats.json")
const META_PATH = path.join(DB_DIR, "chats.sync-meta.json")
const MAX_THREADS = 10

function isNotFound(err: unknown): boolean {
  return Boolean(err && typeof err === "object" && "code" in err && err.code === "ENOENT")
}

// ─── Read / write ─────────────────────────────────────────────────────────────
async function readStore(): Promise<ChatStore> {
  try {
    const data = await fs.readFile(DB_PATH, "utf-8")
    try {
      const parsed = JSON.parse(data) as unknown
      if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) {
        throw new Error("Chat history store root must be an object")
      }
      return parsed as ChatStore
    } catch (parseErr) {
      // Corrupt JSON must NOT be silently wiped — that destroys every user's
      // history. Surface the error to the route instead.
      console.error("[chat-db] corrupt chats.json — refusing to overwrite", parseErr)
      throw new Error("Chat history store is corrupt")
    }
  } catch (err) {
    if (!isNotFound(err)) throw err
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
  const tmpPath = `${DB_PATH}.${Math.random().toString(36).slice(2)}.tmp`
  await fs.writeFile(tmpPath, JSON.stringify(store, null, 2), "utf-8")
  await fs.rename(tmpPath, DB_PATH)
}

async function readSyncMeta(): Promise<SyncMetaStore> {
  try {
    const data = await fs.readFile(META_PATH, "utf-8")
    return JSON.parse(data) as SyncMetaStore
  } catch (err) {
    if (isNotFound(err)) return {}
    // Meta is advisory — a corrupt meta file should not block history reads.
    console.error("[chat-db] corrupt chats.sync-meta.json — resetting", err)
    return {}
  }
}

async function writeSyncMeta(meta: SyncMetaStore): Promise<void> {
  await fs.mkdir(DB_DIR, { recursive: true })
  const tmpPath = `${META_PATH}.${Math.random().toString(36).slice(2)}.tmp`
  await fs.writeFile(tmpPath, JSON.stringify(meta, null, 2), "utf-8")
  await fs.rename(tmpPath, META_PATH)
}

function threadActivity(t: StoredThread): number {
  if (typeof t.updatedAt === "number" && t.updatedAt > 0) return t.updatedAt
  for (let i = t.messages.length - 1; i >= 0; i--) {
    const ts = t.messages[i]?.timestamp
    if (typeof ts === "number" && ts > 0) return ts
  }
  return 0
}

// ─── Public API ───────────────────────────────────────────────────────────────
export async function getThreadsForUser(email: string): Promise<StoredThread[]> {
  const store = await readStore()
  const threads = store[email.toLowerCase()]
  if (!Array.isArray(threads)) return []
  return threads.slice(0, MAX_THREADS)
}

export async function saveThreadsForUser(
  email: string,
  threads: StoredThread[],
  clientSyncAt?: number,
): Promise<{ ok: true } | { ok: false; reason: "stale" }> {
  // Defence-in-depth: strip personal-data content at the server persistence
  // layer even if the client-side redaction in use-aura-chat.ts were bypassed.
  const sanitised = threads.map((t) => ({
    ...t,
    updatedAt: threadActivity(t) || Date.now(),
    messages: t.messages.map((m) =>
      m.is_personal_data
        ? { ...m, content: "[Personal data — not stored]" }
        : m
    ),
  }))

  const sorted = [...sanitised].sort(
    (a, b) => (b.updatedAt ?? 0) - (a.updatedAt ?? 0),
  )

  const userEmail = email.toLowerCase()
  const meta = await readSyncMeta()
  const lastSyncAt = meta[userEmail] ?? 0
  const incomingSync =
    typeof clientSyncAt === "number" && clientSyncAt > 0
      ? clientSyncAt
      : Math.max(Date.now(), ...sorted.map((t) => t.updatedAt ?? 0))

  // Reject out-of-order POSTs so an older in-flight save cannot wipe a newer
  // snapshot (common when two messages finish streaming close together).
  if (incomingSync < lastSyncAt) {
    return { ok: false, reason: "stale" }
  }

  // Client list is authoritative (capped at MAX_THREADS). Replacing — rather
  // than merging — is what lets sidebar deletes and clears survive a refresh.
  const store = await readStore()
  store[userEmail] = sorted.slice(0, MAX_THREADS)
  await writeStore(store)

  meta[userEmail] = incomingSync
  await writeSyncMeta(meta)
  return { ok: true }
}
