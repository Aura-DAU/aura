"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpen, Sparkles, Briefcase, Compass, Users, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const TABS = [
  { id: "academics", label: "Academics", href: "/academics", Icon: BookOpen },
  { id: "co-curricular", label: "Co-curr", href: "/co-curricular", Icon: Sparkles },
  { id: "chat", label: "AURA", href: "/chat", Icon: MessageCircle },
  { id: "placements", label: "Placements", href: "/placements", Icon: Briefcase },
  { id: "career-horizons", label: "Career", href: "/career-horizons", Icon: Compass },
  { id: "alumni", label: "Alumni", href: "/alumni", Icon: Users },
];

export default function StudentBottomNav() {
  const pathname = usePathname() ?? "";
  const activeTab = pathname.split("/").filter(Boolean)[0] ?? "academics";

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-background/95 backdrop-blur border-t border-border flex justify-around py-2 px-2 md:hidden">
      {TABS.map(({ id, label, href, Icon }) => {
        const isActive = activeTab === id;
        const isChat = id === "chat";
        return (
          <Link
            key={id}
            href={href}
            className={cn(
              "flex flex-col items-center gap-0.5 flex-1 min-w-0 py-1 rounded-lg transition-colors",
              isChat && "relative",
            )}
          >
            <Icon
              className={cn(
                "h-5 w-5",
                isActive ? "text-[#E8400C]" : "text-muted-foreground",
                isChat && !isActive && "text-[#E8400C]/80",
              )}
            />
            <span
              className={cn(
                "text-[10px] font-semibold truncate",
                isActive ? "text-[#E8400C]" : "text-muted-foreground",
              )}
            >
              {label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
