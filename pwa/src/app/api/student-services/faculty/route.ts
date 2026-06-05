import { NextResponse } from "next/server";

const FACULTY: Array<{
  fileName: string;
  name: string;
  designation: string;
  specialization: string;
  office: string;
  email: string;
}> = [];

export async function GET() {
  return NextResponse.json(FACULTY);
}
