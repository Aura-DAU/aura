import { getServerSession } from "next-auth"

import { backendUrl } from "@/lib/api/backend"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export const maxDuration = 30

const MAX_BYTES = 5 * 1024 * 1024 // 5 MB — mirrors backend limit

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId || !session.user.role) {
    return Response.json({ error: "Unauthorized" }, { status: 401 })
  }

  // Reject oversized requests before reading the body into memory.
  const contentLength = req.headers.get("content-length")
  if (contentLength) {
    const n = Number(contentLength)
    if (Number.isFinite(n) && n > MAX_BYTES + 256 * 1024) {
      return Response.json({ error: "Payload too large" }, { status: 413 })
    }
  }

  const formData = await req.formData().catch(() => null)
  if (!formData) {
    return Response.json({ error: "Invalid form data" }, { status: 400 })
  }

  const queryText = formData.get("query_text")
  if (!queryText || typeof queryText !== "string" || !queryText.trim()) {
    return Response.json({ error: "query_text is required" }, { status: 400 })
  }

  // Forward the multipart payload verbatim so FastAPI can parse it.
  const forwarded = new FormData()
  forwarded.append("query_text", queryText.trim())

  const image = formData.get("image")
  if (image instanceof Blob && image.size > 0) {
    const filename =
      image instanceof File && image.name ? image.name : "screenshot.png"
    forwarded.append("image", image, filename)
  }

  const internalToken = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/bug-report"), {
      method: "POST",
      headers: { Authorization: `Bearer ${internalToken}` },
      body: forwarded,
    })
  } catch (err) {
    console.error("[bug-report] backend unreachable:", err)
    return Response.json({ error: "Backend unavailable" }, { status: 502 })
  }

  if (!backendRes.ok) {
    const detail = await backendRes.json().catch(() => ({})) as { detail?: string }
    return Response.json(
      { error: detail.detail ?? "Submission failed" },
      { status: backendRes.status >= 500 ? 502 : backendRes.status },
    )
  }

  const json = (await backendRes.json()) as { id?: number; created_at?: string }
  return Response.json(json)
}
