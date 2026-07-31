import { getServerSession } from "next-auth"
import { NextResponse } from "next/server"

import { backendUrl } from "@/lib/api/backend"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

/**
 * DELETE /api/memory?threadId=<id>  — forget one conversation.
 * DELETE /api/memory?all=1          — forget every conversation.
 *
 * Clearing or deleting a chat must also remove the backend's persistent
 * per-user memory block for it, otherwise the cleared conversation keeps being
 * injected into later threads for the whole 90-day retention window.
 *
 * Deliberately not under /api/chat: nginx matches that prefix and applies the
 * chat rate limit and overload shed to it, which would let a load spike reject
 * a privacy action that has nothing to do with chat capacity.
 */
export async function DELETE(req: Request) {
  const session = await getServerSession(authOptions)

  // Only signed-in identities have persistent memory — guests are excluded at
  // the store level by design, so there is nothing to delete and no reason to
  // make the round trip.
  if (!session?.user?.erpId || !session.user.role) {
    return NextResponse.json({ ok: true, deleted: false })
  }

  const url = new URL(req.url)
  const all = url.searchParams.get("all")
  const threadId = url.searchParams.get("threadId")

  let path: string
  if (all === "1" || all === "true") {
    path = "/memory"
  } else if (threadId && threadId.length <= 64) {
    path = `/memory/thread/${encodeURIComponent(threadId)}`
  } else {
    return NextResponse.json({ error: "threadId is required" }, { status: 400 })
  }

  let internalToken: string
  try {
    internalToken = signInternalJwt({
      role: session.user.role,
      erpId: session.user.erpId,
      department: session.user.department,
      email: session.user.email ?? undefined,
    })
  } catch (err) {
    console.error("[memory] failed to mint internal JWT:", err)
    return NextResponse.json({ error: "Internal server error" }, { status: 500 })
  }

  try {
    const backendRes = await fetch(backendUrl(path), {
      method: "DELETE",
      headers: { Authorization: `Bearer ${internalToken}` },
    })
    if (!backendRes.ok) {
      console.error("[memory] backend error:", backendRes.status)
      return NextResponse.json({ error: "Backend error" }, { status: 502 })
    }
    return NextResponse.json(await backendRes.json())
  } catch (err) {
    console.error("[memory] backend unreachable:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
