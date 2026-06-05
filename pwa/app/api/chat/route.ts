import { z } from "zod";

export const runtime = "nodejs";

const HistoryTurnSchema = z.object({
  role: z.enum(["user", "assistant"]),
  content: z.string().min(1).max(8000),
});

const BodySchema = z.object({
  question: z.string().min(1).max(2000),
  history: z.array(HistoryTurnSchema).max(40).optional(),
});

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(request: Request) {
  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Invalid JSON" }, { status: 400 });
  }

  const parsed = BodySchema.safeParse(body);
  if (!parsed.success) {
    return Response.json(
      { error: "Invalid request", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  try {
    const upstream = await fetch(`${BACKEND_URL}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(parsed.data),
    });

    if (!upstream.ok) {
      const detail = await upstream.text().catch(() => "");
      return Response.json(
        { error: "Upstream error", status: upstream.status, detail },
        { status: 502 },
      );
    }

    const data = await upstream.json();
    return Response.json(data);
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    return Response.json(
      { error: "Backend unreachable", detail: msg },
      { status: 502 },
    );
  }
}
