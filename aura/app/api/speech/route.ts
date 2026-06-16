import { backendUrl } from "@/lib/api/backend"

export const maxDuration = 60

export async function POST(req: Request) {
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

  let backendRes: Response
  try {
    backendRes = await fetch(backendUrl("/speech"), {
      method: "POST",
      body: forwarded,
    })
  } catch (err) {
    console.error("[speech] backend unreachable:", err)
    return Response.json({ error: "Backend unavailable" }, { status: 502 })
  }

  if (!backendRes.ok) {
    let detail: string | undefined
    try {
      const json = (await backendRes.json()) as { detail?: string }
      detail = json.detail
    } catch {
      /* non-JSON body */
    }
    return Response.json(
      { error: detail ?? "Transcription failed" },
      { status: backendRes.status },
    )
  }

  const json = (await backendRes.json()) as { text?: string }
  return Response.json({ text: json.text ?? "" })
}
