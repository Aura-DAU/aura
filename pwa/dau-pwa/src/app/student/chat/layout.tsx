import React from "react";

export default function ChatLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="min-h-screen bg-slate-900 text-white">{children}</div>;
}
