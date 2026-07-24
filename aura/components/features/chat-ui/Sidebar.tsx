"use client"

import { AnimatePresence, motion } from "framer-motion"
import { MessageSquare, Plus, Trash2, User, LogOut, LayoutDashboard } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatThread, StudentProfile } from "@/lib/chat-types"
import { useSession, signOut } from "next-auth/react"
import { BrandMark } from "@/components/ui/brand-mark"

interface SidebarProps {
  threads: ChatThread[]
  activeThreadId: string | null
  onSelectThread: (id: string) => void
  onNewChat: () => void
  onDeleteThread: (id: string) => void
  onOpenProfile: () => void
  studentProfile: StudentProfile
  mobileOpen: boolean
  onCloseMobile: () => void
}

export function Sidebar(props: SidebarProps) {
  return (
    <>
      <aside className="hidden w-72 shrink-0 border-r border-theme-gray-light bg-theme-gray md:block">
        <SidebarContent {...props} />
      </aside>

      <AnimatePresence>
        {props.mobileOpen ? (
          <div className="fixed inset-0 z-50 md:hidden">
            <motion.div
              className="absolute inset-0 bg-black/60"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={props.onCloseMobile}
              aria-hidden="true"
            />
            <motion.aside
              className="absolute inset-y-0 left-0 w-72 border-r border-theme-gray-light bg-theme-gray"
              initial={{ x: "-100%" }}
              animate={{ x: 0 }}
              exit={{ x: "-100%" }}
              transition={{ type: "spring", stiffness: 320, damping: 32 }}
            >
              <SidebarContent {...props} />
            </motion.aside>
          </div>
        ) : null}
      </AnimatePresence>
    </>
  )
}

function SidebarContent({
  threads,
  activeThreadId,
  onSelectThread,
  onNewChat,
  onDeleteThread,
  onOpenProfile,
  studentProfile,
  onCloseMobile,
}: SidebarProps) {
  const { data: session } = useSession()
  const displayName = session?.user ? (studentProfile.name || session.user.name || "User") : "Guest Account"
  const displayEmail = session?.user ? (session.user.email ?? "") : "Sign in to get started"

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2.5 px-4 py-4">
        <BrandMark className="size-8 shadow-[0_0_20px_-6px_rgba(244,80,59,0.55)]" />
        <div className="flex flex-col leading-tight">
          <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text font-semibold tracking-tight text-transparent">
            AURA
          </span>
          <span className="text-[10px] text-neutral-500">Your campus AI</span>
        </div>
      </div>

      <div className="flex flex-col gap-2 px-3">
        <button
          type="button"
          onClick={() => {
            onNewChat()
            onCloseMobile()
          }}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2.5 text-sm font-semibold text-black shadow-[0_2px_14px_-6px_rgba(244,80,59,0.5)] transition-all hover:brightness-110 active:scale-[0.98]"
        >
          <Plus className="size-4" />
          New chat
        </button>
        {session?.user && (
          <a
            href="/dashboard"
            onClick={onCloseMobile}
            className="flex w-full items-center justify-center gap-2 rounded-full border border-theme-gray-light bg-theme-black/30 px-4 py-2 text-sm font-medium text-neutral-300 transition-colors hover:border-theme-gray-lighter hover:bg-theme-gray-light hover:text-neutral-100"
          >
            <LayoutDashboard className="size-4 text-theme-yellow" />
            Go to Dashboard
          </a>
        )}
      </div>

      <nav className="chat-v2-scroll mt-4 flex-1 space-y-1 overflow-y-auto px-3 pb-4">
        <p className="mb-2 px-2 text-[10px] font-medium uppercase tracking-wider text-neutral-600">
          Conversations
        </p>
        {threads.length === 0 ? (
          <p className="px-2 py-4 text-xs text-neutral-500">
            No conversations yet.
          </p>
        ) : (
          threads.map((thread) => {
            const active = thread.id === activeThreadId
            return (
              <div
                key={thread.id}
                className={cn(
                  "group relative flex items-center gap-2 rounded-xl px-2.5 py-2 text-sm transition-all duration-150",
                  active
                    ? "bg-theme-gray-light text-neutral-100"
                    : "text-neutral-400 hover:bg-theme-gray-light/55 hover:text-neutral-200",
                )}
              >
                {active ? (
                  <span className="absolute inset-y-1.5 left-0 w-0.5 rounded-full bg-gradient-to-b from-theme-red to-theme-yellow" />
                ) : null}
                <button
                  type="button"
                  onClick={() => {
                    onSelectThread(thread.id)
                    onCloseMobile()
                  }}
                  className="flex min-w-0 flex-1 items-center gap-2 text-left"
                >
                  <MessageSquare className={cn("size-4 shrink-0", active && "text-theme-yellow")} />
                  <span className="truncate">{thread.title}</span>
                </button>
                <button
                  type="button"
                  onClick={() => onDeleteThread(thread.id)}
                  aria-label={`Delete ${thread.title}`}
                  className="shrink-0 rounded-md p-1 text-neutral-500 opacity-0 transition-opacity hover:text-theme-red group-hover:opacity-100 focus-visible:opacity-100 max-md:opacity-100"
                >
                  <Trash2 className="size-3.5" />
                </button>
              </div>
            )
          })
        )}
      </nav>
      <div className="flex items-center gap-2 border-t border-theme-gray-light p-3">
        <button
          type="button"
          onClick={onOpenProfile}
          className="flex min-w-0 flex-1 items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors hover:bg-theme-gray-light"
        >
          <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-theme-gray-lighter to-theme-gray text-neutral-200 ring-1 ring-white/10">
            <User className="size-4" />
          </span>
          <span className="min-w-0 flex-1">
            <span suppressHydrationWarning className="flex items-center gap-1.5 truncate text-sm font-medium text-neutral-100">
              <span className="truncate">{displayName}</span>
              {session?.user?.role && (
                <span className="inline-flex items-center rounded-full border border-theme-yellow/20 bg-theme-yellow/10 px-1.5 py-0.5 text-[10px] font-medium capitalize text-theme-yellow">
                  {session.user.role.replace("faculty_", "").replace("dean_", "dean ")}
                </span>
              )}
            </span>
            {session?.user?.department && (
              <span suppressHydrationWarning className="block truncate text-[10px] text-neutral-400">
                {session.user.department}
              </span>
            )}
            <span suppressHydrationWarning className="block truncate text-xs text-neutral-500">
              {displayEmail}
            </span>
          </span>
        </button>
        {session?.user && (
          <button
            type="button"
            onClick={() => signOut({ callbackUrl: "/login" })}
            aria-label="Sign out"
            className="shrink-0 rounded-lg p-2 text-neutral-400 transition-colors hover:bg-theme-gray-light hover:text-theme-red"
          >
            <LogOut className="size-4" />
          </button>
        )}
      </div>
    </div>
  )
}
