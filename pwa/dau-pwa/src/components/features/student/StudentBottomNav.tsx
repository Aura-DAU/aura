"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { mainTabs } from "./sidebarConfig";

export default function StudentBottomNav() {
  const pathname = usePathname();

  const getActiveTab = () => {
    const segments = pathname.split("/");
    if (segments.length >= 3) {
      return segments[2];
    }
    return "academics";
  };

  const activeTab = getActiveTab();

  // Handcrafted premium SVGs matching each section beautifully
  const renderIcon = (tabId: string, isActive: boolean) => {
    const activeClass = isActive ? "text-primary-dau" : "text-text-muted";
    
    switch (tabId) {
      case "academics":
        return (
          <svg className={`w-5.5 h-5.5 ${activeClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
        );
      case "cocurricular":
        return (
          <svg className={`w-5.5 h-5.5 ${activeClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      case "placements":
        return (
          <svg className={`w-5.5 h-5.5 ${activeClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        );
      case "career-horizons":
        return (
          <svg className={`w-5.5 h-5.5 ${activeClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case "alumni":
        return (
          <svg className={`w-5.5 h-5.5 ${activeClass}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-surface-dau/95 backdrop-blur-lg border-t border-border-dau flex justify-around py-2.5 px-4 md:hidden shadow-lg shadow-black/40">
      {mainTabs.map((tab) => {
        const isActive = activeTab === tab.id;

        return (
          <Link
            key={tab.id}
            href={tab.href}
            className="flex flex-col items-center gap-1 flex-1 min-w-0"
          >
            {renderIcon(tab.id, isActive)}
            <span className={`text-[10px] font-semibold truncate ${
              isActive ? "text-primary-dau font-bold" : "text-text-muted"
            }`}>
              {tab.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
