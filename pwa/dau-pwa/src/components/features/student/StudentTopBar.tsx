"use client";

import React, { useState, useRef, useEffect } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { verticalsConfig } from "./sidebarConfig";
import { useAuth } from "@/lib/auth/authContext";

interface SearchResult {
  label: string;
  href: string;
  section: string;
}

// Flatten all nav items into one searchable list
const allRoutes: SearchResult[] = Object.values(verticalsConfig).flatMap(
  (vertical) =>
    vertical.items.map((item) => ({
      label: item.label,
      href: item.href,
      section: vertical.label,
    }))
);

export default function StudentTopBar() {
  const [searchQuery, setSearchQuery] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    router.replace("/");
  };

  const filteredResults: SearchResult[] = searchQuery.trim()
    ? allRoutes.filter(
        (route) =>
          route.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
          route.section.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : [];

  const handleSelect = (href: string) => {
    router.push(href);
    setSearchQuery("");
    setShowDropdown(false);
    setActiveIndex(-1);
    inputRef.current?.blur();
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!showDropdown) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((prev) =>
        prev < filteredResults.length - 1 ? prev + 1 : prev
      );
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((prev) => (prev > 0 ? prev - 1 : 0));
    } else if (e.key === "Enter") {
      e.preventDefault();
      const target =
        activeIndex >= 0 ? filteredResults[activeIndex] : filteredResults[0];
      if (target) handleSelect(target.href);
    } else if (e.key === "Escape") {
      setShowDropdown(false);
      setSearchQuery("");
      setActiveIndex(-1);
      inputRef.current?.blur();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setActiveIndex(-1);
    setShowDropdown(true);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const hasQuery = searchQuery.trim().length > 0;

  return (
    <header className="sticky top-0 z-40 w-full bg-white border-b border-[#E2E8F0] px-6 py-4 flex items-center justify-between gap-4 text-slate-800 shadow-sm">
      {/* Left: Brand Logo & Title */}
      <div className="flex items-center gap-3 shrink-0">
        <Image
          src="/dau_logo.jpg"
          alt="Dhirubhai Ambani University Logo"
          width={180}
          height={44}
          priority
          className="h-11 w-auto object-contain select-none"
        />
      </div>

      {/* Center: Search Bar */}
      <div
        ref={containerRef}
        className="flex-1 max-w-md mx-6 relative hidden md:block"
      >
        {/* Input */}
        <div
          className={`flex items-center justify-between gap-2 px-5 py-2.5 rounded-full bg-slate-50 border transition-all duration-300 ${
            showDropdown && hasQuery
              ? "border-[#E8400C] ring-1 ring-[#E8400C]/20 bg-white rounded-b-none border-b-transparent"
              : showDropdown
              ? "border-[#E8400C] ring-1 ring-[#E8400C]/20 bg-white"
              : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <input
            ref={inputRef}
            type="text"
            placeholder="Search courses, guidelines, events..."
            className="bg-transparent text-xs text-slate-800 focus:outline-none w-full placeholder-slate-400 font-medium"
            value={searchQuery}
            onChange={handleChange}
            onFocus={() => setShowDropdown(true)}
            onKeyDown={handleKeyDown}
            autoComplete="off"
          />
          {/* Clear button */}
          {hasQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery("");
                setShowDropdown(false);
                setActiveIndex(-1);
                inputRef.current?.focus();
              }}
              className="text-slate-400 hover:text-slate-600 transition-colors duration-150 shrink-0"
            >
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
          <svg
            className="w-4 h-4 text-slate-400 cursor-pointer hover:text-[#E8400C] transition-colors duration-150 shrink-0"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
            onClick={() => {
              if (filteredResults.length > 0) handleSelect(filteredResults[0].href);
            }}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>

        {/* Dropdown */}
        {showDropdown && hasQuery && (
          <div className="absolute left-0 right-0 top-full bg-white border border-[#E8400C] border-t-0 rounded-b-2xl shadow-lg overflow-hidden z-50 max-h-72 overflow-y-auto">
            {filteredResults.length > 0 ? (
              <>
                {filteredResults.map((result, i) => (
                  <button
                    key={result.href}
                    type="button"
                    onMouseDown={(e) => {
                      e.preventDefault(); // prevent blur before click
                      handleSelect(result.href);
                    }}
                    onMouseEnter={() => setActiveIndex(i)}
                    className={`w-full text-left flex items-center justify-between gap-3 px-5 py-3 transition-colors duration-100 ${
                      activeIndex === i
                        ? "bg-orange-50"
                        : "hover:bg-slate-50"
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <svg className="w-3.5 h-3.5 text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                      </svg>
                      <span className="text-xs font-semibold text-slate-800 truncate">
                        {result.label}
                      </span>
                    </div>
                    <span className="text-[10px] font-bold text-[#E8400C] bg-orange-50 border border-orange-100 px-2 py-0.5 rounded-full shrink-0">
                      {result.section}
                    </span>
                  </button>
                ))}
              </>
            ) : (
              <div className="flex flex-col items-center justify-center gap-2 px-5 py-6 text-slate-400">
                <svg className="w-8 h-8 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="text-xs font-semibold">No results found</p>
                <p className="text-[10px]">
                  Try &ldquo;courses&rdquo;, &ldquo;hostel&rdquo;, or &ldquo;placements&rdquo;
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Right: Notifications & User Avatar */}
      <div className="flex items-center gap-5 shrink-0">
        {/* Ask AURA AI Button */}
        <Link
          href="/student/chat"
          className="flex items-center gap-1.5 px-3 py-2 text-[10px] font-black uppercase text-[#E8400C] bg-orange-50 border border-orange-100 hover:bg-orange-100 rounded-full transition-all duration-200 shrink-0"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Ask AURA</span>
        </Link>

        {/* Notifications Bell */}
        <button className="p-2.5 text-slate-500 hover:text-slate-850 rounded-full bg-slate-50 border border-slate-100 hover:bg-slate-100 transition-all duration-200 relative">
          <svg
            className="w-4.5 h-4.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-[#E8400C] text-white text-[10px] font-black rounded-full flex items-center justify-center border-2 border-white">
            3
          </span>
        </button>

        {/* User Profile Info Card */}
        <div className="flex items-center gap-3 group">
          <div className="relative shrink-0">
            <div className="w-9 h-9 rounded-full border border-slate-200 overflow-hidden shadow-sm">
              <div className="w-full h-full bg-orange-50 flex items-center justify-center font-black text-xs text-[#E8400C]">
                {user?.studentId?.slice(0, 2).toUpperCase() ?? "ST"}
              </div>
            </div>
          </div>
          <div className="text-left hidden sm:block leading-tight">
            <p className="text-xs font-black text-slate-800">
              {user?.studentId ?? "Student"}
            </p>
            <p className="text-[9px] text-emerald-600 font-bold mt-0.5 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block" />
              Active
            </p>
          </div>
          {/* Logout button */}
          <button
            onClick={handleLogout}
            title="Sign out"
            className="p-2 text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-full transition-all duration-200 ml-1"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
}
