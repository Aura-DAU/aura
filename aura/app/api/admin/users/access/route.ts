import { NextResponse } from "next/server"
import { getServerSession } from "next-auth"
import { z } from "zod"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"
import { backendUrl } from "@/lib/api/backend"

const grantAccessSchema = z.object({
  email: z.string().email().max(320),
  role: z.literal("admin").optional(),
  erp_id: z.string().min(1).max(64).optional(),
  dept: z.string().max(64).optional(),
})

const revokeAccessSchema = z.object({
  email: z.string().email().max(320),
})

function forbidden() {
  return NextResponse.json({ error: "Forbidden: Admin access required" }, { status: 403 })
}

/** Prefer FastAPI's `detail` field over the raw JSON body for client toasts. */
async function backendErrorMessage(res: Response, fallback: string): Promise<string> {
  const errText = await res.text().catch(() => "")
  if (!errText) return fallback
  try {
    const parsed = JSON.parse(errText) as { detail?: unknown; error?: unknown }
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail
    }
    if (typeof parsed.error === "string" && parsed.error.trim()) {
      return parsed.error
    }
  } catch {
    // Non-JSON backend body — return as-is.
  }
  return errText
}

export async function GET() {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return forbidden()
  }

  const internalToken = await signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  try {
    const res = await fetch(backendUrl("/admin/users/access"), {
      headers: { Authorization: `Bearer ${internalToken}` },
      cache: "no-store",
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to fetch admin users" }, { status: res.status })
      }
      return NextResponse.json(
        { error: await backendErrorMessage(res, "Failed to fetch admin users") },
        { status: res.status },
      )
    }

    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[admin API] fetch admin access list error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return forbidden()
  }

  let rawBody: unknown
  try {
    rawBody = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = grantAccessSchema.safeParse(rawBody)
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid grant access payload" }, { status: 400 })
  }

  const internalToken = await signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  try {
    const res = await fetch(backendUrl("/admin/users/access"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${internalToken}`,
      },
      body: JSON.stringify(parsed.data),
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to grant admin access" }, { status: res.status })
      }
      return NextResponse.json(
        { error: await backendErrorMessage(res, "Failed to grant admin access") },
        { status: res.status },
      )
    }

    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[admin API] grant admin access error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function DELETE(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user || session.user.role !== "admin") {
    return forbidden()
  }

  let rawBody: unknown
  try {
    rawBody = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const parsed = revokeAccessSchema.safeParse(rawBody)
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid revoke access payload" }, { status: 400 })
  }

  const internalToken = await signInternalJwt({
    role: "admin",
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  try {
    const res = await fetch(backendUrl("/admin/users/access"), {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${internalToken}`,
      },
      body: JSON.stringify(parsed.data),
    })

    if (!res.ok) {
      if (res.status >= 500) {
        return NextResponse.json({ error: "Failed to revoke admin access" }, { status: res.status })
      }
      return NextResponse.json(
        { error: await backendErrorMessage(res, "Failed to revoke admin access") },
        { status: res.status },
      )
    }

    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[admin API] revoke admin access error:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
