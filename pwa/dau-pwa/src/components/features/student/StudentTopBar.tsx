"use client";

import React, { useState } from "react";
import Image from "next/image";
import Link from "next/link";

export default function StudentTopBar() {
  const [searchFocused, setSearchFocused] = useState(false);

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
      <div className="flex-1 max-w-md mx-6 relative hidden md:block">
        <div
          className={`flex items-center justify-between gap-2 px-5 py-2.5 rounded-full bg-slate-50 border transition-all duration-300 ${
            searchFocused
              ? "border-[#E8400C] ring-1 ring-[#E8400C]/20 bg-white"
              : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <input
            type="text"
            placeholder="Search courses, guidelines, events..."
            className="bg-transparent text-xs text-slate-800 focus:outline-none w-full placeholder-slate-400 font-medium"
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
          />
          <svg
            className="w-4 h-4 text-slate-400 cursor-pointer hover:text-slate-600 transition-colors duration-150"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </div>
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
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="relative shrink-0">
            <div className="w-9 h-9 rounded-full border border-slate-200 overflow-hidden shadow-sm group-hover:scale-105 transition-transform duration-200">
              <div className="w-full h-full bg-orange-50 flex items-center justify-center font-black text-xs text-[#E8400C]">
                RS
              </div>
            </div>
          </div>
          <div className="text-left hidden sm:block leading-tight">
            <p className="text-xs font-black text-slate-800 group-hover:text-[#E8400C] transition-colors duration-150">
              Rahul Sharma
            </p>
            <p className="text-[9px] text-emerald-600 font-bold mt-0.5 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 inline-block animate-pulse" />
              Active
            </p>
          </div>
        </div>
      </div>
    </header>
  );
}
