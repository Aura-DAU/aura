"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { mainTabs } from "./sidebarConfig";

export default function StudentVerticalTabs() {
  const pathname = usePathname();

  const getActiveTab = () => {
    const segments = pathname.split("/");
    if (segments.length >= 3) {
      return segments[2];
    }
    return "academics";
  };

  const activeTab = getActiveTab();

  return (
    <nav className="w-full bg-white border-b border-[#E2E8F0] px-8 py-4.5 hidden md:flex items-center gap-3.5 overflow-x-auto">
      {mainTabs.map((tab) => {
        const isActive = activeTab === tab.id;

        return (
          <Link
            key={tab.id}
            href={tab.href}
            className={`px-7 py-2.5 rounded-full text-xs font-black tracking-wide uppercase transition-all duration-200 text-center ${
              isActive
                ? "bg-[#E8400C] text-white shadow-lg shadow-[#E8400C]/25 hover:scale-[1.02]"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900 hover:scale-[1.02]"
            }`}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
