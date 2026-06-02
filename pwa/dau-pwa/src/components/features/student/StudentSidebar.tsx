"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { verticalsConfig } from "./sidebarConfig";

export default function StudentSidebar() {
  const pathname = usePathname();

  const getActiveVerticalKey = () => {
    const segments = pathname.split("/");
    if (segments.length >= 3) {
      const verticalKey = segments[2];
      if (verticalsConfig[verticalKey]) {
        return verticalKey;
      }
    }
    return "academics";
  };

  const activeKey = getActiveVerticalKey();
  const config = verticalsConfig[activeKey];

  if (!config) return null;

  return (
    <aside className="w-64 shrink-0 bg-white text-slate-800 hidden md:block min-h-[calc(100vh-140px)] p-6 rounded-r-[32px] shadow-sm border-r border-[#E2E8F0] m-4 mr-0">
      <div className="space-y-6">
        <div>
          <h2 className="text-[10px] font-black text-[#E8400C] tracking-widest uppercase mb-1">
            {config.label}
          </h2>
          <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">
            Portal Navigation
          </p>
        </div>

        <nav className="space-y-1.5">
          {config.items.map((item, idx) => {
            const isSubActive =
              pathname === item.href ||
              (pathname.startsWith(item.href) &&
                item.href !== `/student/${activeKey}`);

            return (
              <Link
                key={idx}
                href={item.href}
                className={`flex items-center gap-3 px-4 py-3 rounded-xl text-xs font-bold transition-all duration-200 ${
                  isSubActive
                    ? "bg-orange-50 text-[#E8400C] shadow-sm font-black border-l-4 border-l-[#E8400C] pl-3.5"
                    : "text-slate-600 hover:text-[#E8400C] hover:bg-slate-50/50"
                }`}
              >
                <span>{item.label}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
