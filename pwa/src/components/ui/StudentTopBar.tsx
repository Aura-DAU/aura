"use client";

import React from "react";
import Image from "next/image";
import Link from "next/link";
import { Bell, Search, Sparkles } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button, buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";

export default function StudentTopBar() {
  return (
    <header className="sticky top-0 z-40 w-full bg-background border-b border-border px-6 py-3 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 shrink-0">
        <Image
          src="/dau_logo.jpg"
          alt="Dhirubhai Ambani University"
          width={180}
          height={44}
          priority
          className="h-10 w-auto object-contain select-none"
        />
      </div>

      <div className="flex-1 max-w-md mx-6 relative hidden md:block">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="search"
          placeholder="Search courses, guidelines, events..."
          className="pl-9 rounded-full bg-muted/40 border-transparent focus-visible:bg-background"
        />
      </div>

      <div className="flex items-center gap-3 shrink-0">
        <Link
          href="/chat"
          className={cn(
            buttonVariants({ size: "sm" }),
            "rounded-full bg-[#E8400C] text-white hover:bg-[#D7380A] gap-1.5 shadow-sm shadow-[#E8400C]/20",
          )}
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span className="text-xs font-bold">Ask AURA</span>
        </Link>

        <Button variant="ghost" size="icon" className="relative rounded-full" aria-label="Notifications">
          <Bell className="h-4 w-4" />
          <Badge className="absolute -top-0.5 -right-0.5 h-4 min-w-4 px-1 text-[9px] font-bold bg-[#E8400C] text-white border-2 border-background rounded-full">
            3
          </Badge>
        </Button>

        <div className="hidden sm:flex items-center gap-2.5 group cursor-pointer">
          <Avatar className="h-9 w-9 border border-border">
            <AvatarFallback className="bg-orange-50 text-[#E8400C] font-bold text-xs">RS</AvatarFallback>
          </Avatar>
          <div className="text-left leading-tight">
            <p className="text-xs font-bold text-foreground group-hover:text-[#E8400C] transition-colors">
              Rahul Sharma
            </p>
            <p className="text-[10px] text-emerald-600 font-semibold flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
              Active
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
