import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  const audioBase64 = body?.audioBase64 as string | undefined;
  const filename = (body?.filename as string | undefined) ?? "audio.webm";

  if (!audioBase64) {
    return NextResponse.json({ success: false, error: "Missing audioBase64" }, { status: 400 });
  }

  const apiKey = process.env.OPEN_AI_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ success: false, error: "OPEN_AI_API_KEY not configured" }, { status: 500 });
  }

  try {
    const buffer = Buffer.from(audioBase64, "base64");
    const mime = filename.endsWith(".wav") ? "audio/wav" : "audio/webm";
    const blob = new Blob([buffer], { type: mime });

    const form = new FormData();
    form.append("file", blob, filename);
    form.append("model", "whisper-1");

    const res = await fetch("https://api.openai.com/v1/audio/transcriptions", {
      method: "POST",
      headers: { Authorization: `Bearer ${apiKey}` },
      body: form,
    });

    if (!res.ok) {
      const errText = await res.text();
      return NextResponse.json(
        { success: false, error: `OpenAI ${res.status}: ${errText}` },
        { status: 502 },
      );
    }

    const data = (await res.json()) as { text?: string };
    return NextResponse.json({ success: true, text: data.text ?? "" });
  } catch (e) {
    return NextResponse.json(
      { success: false, error: e instanceof Error ? e.message : "transcription failed" },
      { status: 500 },
    );
  }
}
