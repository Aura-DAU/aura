import { NextResponse } from "next/server";

export async function GET(req: Request) {
  const file = new URL(req.url).searchParams.get("file") ?? "";
  return NextResponse.json({
    success: true,
    content: `# Course content stub\n\nRequested file: \`${file}\`\n\nReplace this stub with real document loading.`,
  });
}
