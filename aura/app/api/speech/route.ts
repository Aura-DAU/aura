import { getServerSession } from "next-auth"

import { backendUrl } from "@/lib/api/backend"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export const maxDuration = 60

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId || !session.user.role) {
    return Response.json({ error: "Unauthorized" }, { status: 401 })
  }

  const formData = await req.formData().catch(() => null)
  const file = formData?.get("audio")

  if (!(file instanceof Blob)) {
    return Response.json({ error: "No audio file provided" }, { status: 400 })
  }

  const MAX_BYTES = 25 * 1024 * 1024
  if (file.size > MAX_BYTES) {
    return Response.json({ error: "Audio file too large" }, { status: 413 })
  }

  const filename =
    file instanceof File && file.name ? file.name : "recording.webm"

  const forwarded = new FormData()
  forwarded.append("file", file, filename)

  const internalToken = signInternalJwt({
    role: session.user.role,
    erpId: session.user.erpId,
    department: session.user.department,
    email: session.user.email ?? undefined,
  })

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/speech"), {
      method: "POST",
      headers: {
        Authorization: `Bearer ${internalToken}`,
      },
      body: forwarded,
    })
  } catch (err) {
    console.error("[speech] backend unreachable:", err)
    return Response.json({ error: "Backend unavailable" }, { status: 502 })
  }

  if (!backendRes.ok) {
    console.error("[speech] backend error:", backendRes.status)
    return Response.json(
      { error: "Transcription failed" },
      { status: backendRes.status >= 500 ? 502 : backendRes.status },
    )
  }

  const json = (await backendRes.json()) as { text?: string }
  return Response.json({ text: json.text ?? "" })
}
