"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { verticalsConfig } from "./sidebarConfig";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";

export default function StudentSidebar() {
  const pathname = usePathname() ?? "";

  const getActiveVerticalKey = () => {
    const segments = pathname.split("/").filter(Boolean);
    const key = segments[0];
    return key && verticalsConfig[key] ? key : "academics";
  };

  const activeKey = getActiveVerticalKey();
  const config = verticalsConfig[activeKey];
  if (!config) return null;

  return (
    <aside className="w-64 shrink-0 hidden md:block">
      <div className="sticky top-[73px] m-4 mr-0 p-5 rounded-2xl border border-border bg-card shadow-sm">
        <div className="mb-4">
          <h2 className="text-[10px] font-bold text-[#E8400C] tracking-widest uppercase">
            {config.label}
          </h2>
          <p className="text-[9px] text-muted-foreground font-semibold uppercase tracking-wider mt-0.5">
            Portal Navigation
          </p>
        </div>
        <Separator className="mb-3" />
        <ScrollArea className="h-[calc(100vh-220px)] pr-2">
          <nav className="space-y-1">
            {config.items.map((item) => {
              const isActive =
                pathname === item.href ||
                (pathname.startsWith(`${item.href}/`) && item.href !== `/${activeKey}`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "block px-3 py-2.5 rounded-lg text-xs font-semibold transition-colors",
                    isActive
                      ? "bg-orange-50 text-[#E8400C] border-l-2 border-[#E8400C] pl-[10px]"
                      : "text-muted-foreground hover:text-foreground hover:bg-muted/60",
                  )}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </ScrollArea>
      </div>
    </aside>
  );
}
