import { getServerSession, type Session } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

function buildToken(session: Session | null) {
  if (!session?.user?.erpId) return null
  return signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    fullName: session.user.fullName,
    currentYear: session.user.currentYear,
    currentSem: session.user.currentSem,
    currentSec: session.user.currentSec,
  })
}

type PublicSyncState = "idle" | "syncing" | "completed" | "failed"

interface BackendSyncStatus {
  status?: unknown
  created?: unknown
  updated?: unknown
  removed?: unknown
  errors?: unknown
}

function count(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0
}

function publicSyncState(status: unknown): PublicSyncState {
  if (status === "PENDING" || status === "RUNNING") return "syncing"
  if (status === "COMPLETED") return "completed"
  if (status === "FAILED" || status === "CANCELLED") return "failed"
  return "idle"
}

export async function GET() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/calendar/timetable/sync/status"), {
      cache: "no-store",
      headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) {
      return NextResponse.json({ error: "Could not check calendar sync" }, { status: res.status })
    }

    const data = (await res.json()) as BackendSyncStatus
    return NextResponse.json({
      state: publicSyncState(data.status),
      created: count(data.created),
      updated: count(data.updated),
      removed: count(data.removed),
      hasWarnings: Array.isArray(data.errors) && data.errors.length > 0,
    })
  } catch (err) {
    console.error("[calendar/timetable/sync] GET failed:", err)
    return NextResponse.json({ error: "Calendar sync status unavailable" }, { status: 502 })
  }
}

export async function POST() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/calendar/timetable/sync"), {
      method: "POST",
      headers: { "Authorization": `Bearer ${token}` },
    })
    if (!res.ok) {
      let errDetail = "Failed to sync timetable"
      try {
        const errJson = await res.json()
        if (errJson?.detail) errDetail = errJson.detail
      } catch {
        // ignore
      }
      return NextResponse.json({ error: errDetail }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[calendar/timetable/sync] POST failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function DELETE() {
  const session = await getServerSession(authOptions)
  const token = buildToken(session)
  if (!token) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  try {
    const res = await fetch(backendUrl("/calendar/timetable/sync"), {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${token}` },
    })
    if (!res.ok) {
      return NextResponse.json({ error: "Failed to unsync timetable" }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[calendar/timetable/sync] DELETE failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
