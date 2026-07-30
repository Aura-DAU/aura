import { getServerSession } from "next-auth"

import { backendUrl } from "@/lib/api/backend"
import { authOptions } from "@/lib/auth/options"
import { signInternalJwt } from "@/lib/auth/internal-jwt"

export const maxDuration = 60

// Mirror server/api/api.py ALLOWED_AUDIO — reject early to cut abuse bandwidth.
const ALLOWED_AUDIO_EXT = new Set([".wav", ".mp3", ".m4a", ".webm", ".ogg", ".flac"])
const ALLOWED_AUDIO_MIME = new Set([
  "audio/wav",
  "audio/wave",
  "audio/x-wav",
  "audio/mpeg",
  "audio/mp3",
  "audio/mp4",
  "audio/m4a",
  "audio/x-m4a",
  "audio/webm",
  "audio/ogg",
  "audio/flac",
  "video/webm", // MediaRecorder often labels webm audio this way
])

function extensionOf(name: string): string {
  const i = name.lastIndexOf(".")
  return i >= 0 ? name.slice(i).toLowerCase() : ""
}

export async function POST(req: Request) {
  const session = await getServerSession(authOptions)
  if (!session?.user?.erpId || !session.user.role) {
    return Response.json({ error: "Unauthorized" }, { status: 401 })
  }

  // Reject before buffering multipart into memory when Content-Length is present.
  const MAX_BYTES = 25 * 1024 * 1024
  const contentLength = req.headers.get("content-length")
  if (contentLength) {
    const n = Number(contentLength)
    // Allow modest multipart framing overhead on top of the audio cap.
    if (Number.isFinite(n) && n > MAX_BYTES + 256 * 1024) {
      return Response.json({ error: "Audio file too large" }, { status: 413 })
    }
  }

  const formData = await req.formData().catch(() => null)
  const file = formData?.get("audio")

  if (!(file instanceof Blob)) {
    return Response.json({ error: "No audio file provided" }, { status: 400 })
  }

  if (file.size > MAX_BYTES) {
    return Response.json({ error: "Audio file too large" }, { status: 413 })
  }

  const filename =
    file instanceof File && file.name ? file.name : "recording.webm"
  const ext = extensionOf(filename)
  if (!ALLOWED_AUDIO_EXT.has(ext)) {
    return Response.json({ error: `Unsupported file type: ${ext || "(none)"}` }, { status: 400 })
  }
  if (file.type && !ALLOWED_AUDIO_MIME.has(file.type.toLowerCase())) {
    return Response.json({ error: `Unsupported content type: ${file.type}` }, { status: 400 })
  }

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
