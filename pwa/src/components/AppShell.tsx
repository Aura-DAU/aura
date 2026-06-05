"use client";

import React from "react";
import { usePathname } from "next/navigation";
import StudentTopBar from "@/components/ui/StudentTopBar";
import StudentVerticalTabs from "@/components/ui/StudentVerticalTabs";
import StudentSidebar from "@/components/ui/StudentSidebar";
import StudentBottomNav from "@/components/ui/StudentBottomNav";

const PORTAL_PREFIXES = ["/academics", "/co-curricular", "/placements", "/career-horizons", "/alumni"];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname() ?? "";

  if (pathname.startsWith("/chat")) {
    return <div className="min-h-screen bg-slate-900 text-white">{children}</div>;
  }

  const isPortal = PORTAL_PREFIXES.some((p) => pathname === p || pathname.startsWith(`${p}/`));
  if (!isPortal) {
    return <>{children}</>;
  }

  return (
    <div className="flex flex-col min-h-screen bg-background text-foreground relative">
      <StudentTopBar />
      <StudentVerticalTabs />
      <div className="flex flex-1 relative">
        <StudentSidebar />
        <main className="flex-1 w-full p-4 sm:p-6 md:p-8 pb-20 md:pb-8 overflow-y-auto">
          <div className="max-w-6xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
      <StudentBottomNav />
    </div>
  );
}
