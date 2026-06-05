import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json().catch(() => null);
  const message = body?.message ?? "";

  const fastapiUrl = process.env.FASTAPI_RAG_URL;
  if (fastapiUrl) {
    try {
      const res = await fetch(`${fastapiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (res.ok) {
        return NextResponse.json(await res.json());
      }
    } catch (err) {
      console.error("FastAPI RAG backend unreachable:", err);
    }
  }

  return NextResponse.json({
    success: true,
    content: `(stub) AURA backend not wired yet. You asked: "${message}"`,
    citations: [],
  });
}
