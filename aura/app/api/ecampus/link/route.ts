import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth/options"
import { backendUrl } from "@/lib/api/backend"
import { NextResponse } from "next/server"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export async function GET(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const token = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
  })

  try {
    const res = await fetch(backendUrl("/ecampus/link"), {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    })

    if (!res.ok) {
      const errText = await res.text()
      return NextResponse.json({ error: errText || "Failed to fetch linking status" }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[ecampus-link] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const token = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
  })

  let body
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: "Invalid JSON" }, { status: 400 })
  }

  const { ecampus_username, ecampus_password } = body
  if (!ecampus_username || !ecampus_password) {
    return NextResponse.json({ error: "Username and password are required" }, { status: 400 })
  }

  try {
    const res = await fetch(backendUrl("/ecampus/link"), {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
      },
      body: JSON.stringify({ ecampus_username, ecampus_password }),
    })

    if (!res.ok) {
      let errDetail = "Failed to link eCampus account"
      try {
        const errJson = await res.json()
        if (errJson?.detail) errDetail = errJson.detail
      } catch {
        const errText = await res.text().catch(() => "")
        if (errText) errDetail = errText
      }
      return NextResponse.json({ error: errDetail }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[ecampus-link] POST failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}

export async function DELETE(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const token = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
  })

  try {
    const res = await fetch(backendUrl("/ecampus/link"), {
      method: "DELETE",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    })

    if (!res.ok) {
      const errText = await res.text()
      return NextResponse.json({ error: errText || "Failed to unlink eCampus account" }, { status: res.status })
    }

    const data = await res.json()
    return NextResponse.json(data)
  } catch (err) {
    console.error("[ecampus-link] DELETE failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
