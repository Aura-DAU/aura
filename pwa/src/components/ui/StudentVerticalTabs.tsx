"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { mainTabs } from "./sidebarConfig";
import { cn } from "@/lib/utils";

export default function StudentVerticalTabs() {
  const pathname = usePathname() ?? "";
  const activeTab = pathname.split("/").filter(Boolean)[0] ?? "academics";

  return (
    <nav className="w-full bg-background border-b border-border px-6 py-3 hidden md:flex items-center gap-2 overflow-x-auto">
      {mainTabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <Link
            key={tab.id}
            href={tab.href}
            className={cn(
              "px-5 py-2 rounded-full text-xs font-bold uppercase tracking-wide transition-all",
              isActive
                ? "bg-[#E8400C] text-white shadow-sm shadow-[#E8400C]/25 scale-[1.02]"
                : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
