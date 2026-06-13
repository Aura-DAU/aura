import React from "react";
import { StudentProfile } from "@/app/api/chat.service";
import { UserSession } from "@/hooks/use-aura-chat";

interface ChatSidebarProps {
  open: boolean;
  onClose: () => void;
  collapsed?: boolean;
  recentQueries: string[];
  onSelectQuery: (query: string) => void;
  studentProfile: StudentProfile;
  onOpenProfile: () => void;
  onClearChat: () => void;
  userSession?: UserSession | null;
}

function DAUCrest({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 40 40"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="40" height="40" rx="6" fill="#1a3a5c" />
      <path
        d="M20 9 L30 13 V20 C30 26 25.5 30 20 31.5 C14.5 30 10 26 10 20 V13 Z"
        stroke="#ffffff"
        strokeWidth="1.6"
        fill="none"
      />
      <path
        d="M20 14 L20 26 M14.5 17.5 L25.5 17.5"
        stroke="#ffffff"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
    </svg>
  );
}

export default function ChatSidebar({
  open,
  onClose,
  collapsed = false,
  recentQueries,
  onSelectQuery,
  studentProfile,
  onOpenProfile,
  onClearChat,
  userSession
}: ChatSidebarProps) {
  const getInitials = () => {
    const name = userSession ? userSession.name : studentProfile.name;
    if (!name) return "?";
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  };

  const getDisplayName = () => {
    if (userSession) return userSession.name;
    return studentProfile.name || "Guest Account";
  };

  const getSubtext = () => {
    if (userSession) {
      if (userSession.role === "parent") {
        return `Parent of ${studentProfile.name || "Student"}`;
      }
      return `${studentProfile.branch || "B.Tech"} - ${studentProfile.semester || "Sem V"}`;
    }
    return studentProfile.name ? `${studentProfile.branch} - ${studentProfile.semester}` : "Configure profile settings";
  };

  return (
    <aside
      className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800 transition-transform duration-200 lg:static lg:translate-x-0 ${
        open ? "translate-x-0" : "-translate-x-full"
      } ${collapsed ? "lg:hidden" : ""}`}
    >
      <div className="flex h-16 items-center justify-between px-5 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center gap-2.5">
          <DAUCrest className="w-8 h-8 shrink-0" />
          <div className="leading-tight">
            <h1 className="text-sm font-semibold text-slate-900 dark:text-slate-100">AURA</h1>
            <span className="text-[12px] text-slate-500 dark:text-slate-400">
              DA-IICT Academic Assistant
            </span>
          </div>
        </div>
        <button
          onClick={onClose}
          className="rounded-md p-1.5 text-slate-500 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-slate-100 lg:hidden hover:cursor-pointer"
          type="button"
        >
          <svg
            className="w-5 h-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      </div>

      <div className="px-3 py-3">
        <button
          onClick={onClearChat}
          type="button"
          className="flex w-full items-center justify-center gap-2.5 rounded-md border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-700 px-3.5 py-2.5 text-sm font-medium text-slate-700 dark:text-slate-200 transition-colors duration-150 hover:cursor-pointer"
        >
          <svg
            className="w-4 h-4 text-slate-500"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 4.5v15m7.5-7.5h-15"
            />
          </svg>
          New chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-0.5">
        <span className="block px-3 text-xs font-medium text-slate-500 dark:text-slate-400 mb-1.5">
          Recent
        </span>
        {recentQueries.map((thread, idx) => (
          <button
            key={idx}
            onClick={() => onSelectQuery(thread)}
            type="button"
            className="flex w-full items-center rounded-md px-3 py-2 text-left text-sm text-slate-600 dark:text-slate-300 hover:bg-slate-200/70 dark:hover:bg-slate-800 hover:text-slate-900 dark:hover:text-white transition-colors duration-150 hover:cursor-pointer"
          >
            <span className="truncate">{thread}</span>
          </button>
        ))}
      </div>

      <div className="p-3 border-t border-slate-200 dark:border-slate-800">
        <button
          onClick={onOpenProfile}
          type="button"
          className="flex w-full items-center gap-3 rounded-md hover:bg-slate-200/70 dark:hover:bg-slate-800 p-2.5 text-left transition-colors duration-150 text-slate-900 dark:text-slate-100 hover:cursor-pointer"
        >
          <div className="w-8 h-8 rounded-md bg-brand-50 dark:bg-brand-900/30 text-brand-600 dark:text-brand-400 flex items-center justify-center font-semibold text-xs border border-brand-100 dark:border-brand-800 shrink-0">
            {getInitials()}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-slate-800 dark:text-slate-200 truncate">
              {getDisplayName()}
            </p>
            <p className="text-xs text-slate-500 truncate">
              {getSubtext()}
            </p>
          </div>
          <svg
            className="w-4 h-4 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
        </button>
      </div>
    </aside>
  );
}
