import React from "react";
import Link from "next/link";
import { StudentProfile } from "@/services/chat";

interface ChatSidebarProps {
  open: boolean;
  onClose: () => void;
  recentQueries: string[];
  onSelectQuery: (query: string) => void;
  studentProfile: StudentProfile;
  onOpenProfile: () => void;
  onClearChat: () => void;
}

export default function ChatSidebar({
  open,
  onClose,
  recentQueries,
  onSelectQuery,
  studentProfile,
  onOpenProfile,
  onClearChat,
}: ChatSidebarProps) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-slate-950 border-r border-slate-800/80 transition-transform duration-300 lg:static lg:translate-x-0 ${
        open ? "translate-x-0" : "-translate-x-full"
      }`}
    >
      <div className="flex h-16 items-center justify-between px-6 border-b border-slate-900">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-xl bg-primary-dau text-white font-black text-sm flex items-center justify-center shadow-lg shadow-primary-dau/25">
            A
          </span>
          <div>
            <h1 className="text-sm font-black tracking-tight text-white">AURA Assistant</h1>
            <span className="text-[9px] font-black uppercase tracking-wider text-primary-dau">
              DAU PWA Registry
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-900 hover:text-white lg:hidden"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="px-4 py-4">
        <button
          onClick={onClearChat}
          className="flex w-full items-center gap-2.5 rounded-xl border border-slate-800 bg-slate-900 hover:bg-slate-850 px-4 py-3 text-xs font-black uppercase tracking-wider text-slate-200 transition-all duration-150 hover:border-primary-dau/30 hover:text-white"
        >
          <svg className="w-4 h-4 text-primary-dau" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4.5v15m7.5-7.5h-15" />
          </svg>
          New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1.5 scrollbar-thin scrollbar-thumb-slate-850">
        <span className="block px-3 text-[9px] font-black uppercase tracking-wider text-slate-500 mb-2">
          Recent Queries
        </span>
        {recentQueries.map((thread, idx) => (
          <button
            key={idx}
            onClick={() => onSelectQuery(thread)}
            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-xs font-medium text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-all duration-150 group"
          >
            <svg className="w-4.5 h-4.5 text-slate-600 group-hover:text-slate-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <span className="truncate">{thread}</span>
          </button>
        ))}
      </div>

      <div className="p-4 border-t border-slate-900">
        <button
          onClick={onOpenProfile}
          className="flex w-full items-center gap-3 rounded-xl bg-slate-900/60 hover:bg-slate-900 border border-slate-900 hover:border-slate-800 p-3 text-left transition-all duration-150 text-slate-100"
        >
          <div className="w-8 h-8 rounded-lg bg-orange-500/10 text-orange-400 flex items-center justify-center font-bold text-xs border border-orange-500/20 shrink-0">
            {studentProfile.name.split(" ").map((n) => n[0]).join("")}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-black text-slate-200 truncate">{studentProfile.name}</p>
            <p className="text-[9px] text-slate-505 font-bold truncate uppercase">{studentProfile.branch}</p>
          </div>
          <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>

        <Link
          href="/student/academics"
          className="flex w-full items-center justify-center gap-2 mt-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 py-2.5 text-[10px] font-black uppercase tracking-wider text-slate-400 hover:text-white transition-colors"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M11 15l-3-3m0 0l3-3m-3 3h8M3 12a9 9 0 1118 0 9 9 0 01-18 0z" />
          </svg>
          Exit to Student Portal
        </Link>
      </div>
    </aside>
  );
}
