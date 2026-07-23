import { NextResponse } from "next/server"
import { backendUrl } from "@/lib/api/backend"

export async function GET() {
  try {
    const res = await fetch(backendUrl("/push/vapid-public-key"), {
      cache: "no-store",
    })
    if (!res.ok) {
      return NextResponse.json({ error: "VAPID key not configured" }, { status: res.status })
    }
    return NextResponse.json(await res.json())
  } catch (err) {
    console.error("[push/vapid-public-key] GET failed:", err)
    return NextResponse.json({ error: "Backend unavailable" }, { status: 502 })
  }
}
