import { NextResponse } from "next/server";

const EVENTS: Array<{
  fileName: string;
  title: string;
  category: string;
  date: string;
}> = [];

export async function GET() {
  return NextResponse.json(EVENTS);
}
