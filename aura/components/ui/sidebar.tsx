"use client"

import { AnimatePresence, motion } from "framer-motion"
import { Download, MessageSquare, Plus, Trash2, User, LogOut, LayoutDashboard } from "lucide-react"
import { cn } from "@/lib/utils"
import type { ChatThread, StudentProfile } from "@/lib/chat-types"
import { useSession, signOut } from "next-auth/react"
import { BrandMark } from "@/components/ui/brand-mark"
import { usePWAInstall } from "@/hooks/use-pwa-install"

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
  const { canInstall, promptInstall } = usePWAInstall()
  const displayName = session?.user ? (studentProfile.name || session.user.name || "User") : "Guest Account"
  const displayEmail = session?.user ? (session.user.email ?? "") : "Sign in to get started"

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-2 px-4 py-4">
        <BrandMark className="size-8 text-sm" />
        <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text font-semibold text-transparent">
          AURA
        </span>
      </div>

      <div className="px-3 flex flex-col gap-2">
        <button
          type="button"
          onClick={() => {
            onNewChat()
            onCloseMobile()
          }}
          className="flex w-full items-center justify-center gap-2 rounded-full bg-gradient-to-r from-theme-red to-theme-yellow px-4 py-2.5 text-sm font-semibold text-black transition-opacity hover:opacity-90"
        >
          <Plus className="size-4" />
          New chat
        </button>
        {session?.user && (
          <a
            href="/dashboard"
            onClick={onCloseMobile}
            className="flex w-full items-center justify-center gap-2 rounded-full border border-theme-gray-light bg-theme-gray-light/30 px-4 py-2 text-sm font-medium text-neutral-300 transition-colors hover:bg-theme-gray-light hover:text-neutral-100"
          >
            <LayoutDashboard className="size-4 text-theme-yellow" />
            Go to Dashboard
          </a>
        )}
        {canInstall ? (
          <button
            type="button"
            onClick={() => {
              void promptInstall()
              onCloseMobile()
            }}
            className="install-aura-glow flex w-full items-center justify-center gap-2 rounded-full border border-theme-yellow/40 bg-theme-yellow/10 px-4 py-2.5 text-sm font-semibold text-theme-yellow transition-all hover:bg-theme-yellow/20 hover:text-theme-yellow"
          >
            <Download className="size-4" />
            Install AURA
          </button>
        ) : null}
      </div>

      <nav className="mt-4 flex-1 space-y-1 overflow-y-auto px-3 pb-4">
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
                  "group flex items-center gap-2 rounded-xl px-2.5 py-2 text-sm transition-colors",
                  active
                    ? "bg-theme-gray-light text-neutral-100"
                    : "text-neutral-400 hover:bg-theme-gray-light/60 hover:text-neutral-200",
                )}
              >
                <button
                  type="button"
                  onClick={() => {
                    onSelectThread(thread.id)
                    onCloseMobile()
                  }}
                  className="flex min-w-0 flex-1 items-center gap-2 text-left"
                >
                  <MessageSquare className="size-4 shrink-0" />
                  <span className="truncate">{thread.title}</span>
                  {active ? (
                    <span className="ml-auto size-1.5 shrink-0 rounded-full bg-theme-yellow" />
                  ) : null}
                </button>
                <button
                  type="button"
                  onClick={() => onDeleteThread(thread.id)}
                  aria-label={`Delete ${thread.title}`}
                  className="shrink-0 rounded-md p-1 text-neutral-500 opacity-0 transition-opacity hover:text-theme-red group-hover:opacity-100"
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
          className="flex flex-1 items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors hover:bg-theme-gray-light min-w-0"
        >
          <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-theme-gray-lighter text-neutral-200">
            <User className="size-4" />
          </span>
          <span className="min-w-0 flex-1">
            <span suppressHydrationWarning className="flex items-center gap-1.5 truncate text-sm font-medium text-neutral-100">
              <span className="truncate">{displayName}</span>
              {session?.user?.role && (
                <span className="inline-flex items-center rounded-full bg-neutral-500/10 px-1.5 py-0.5 text-[10px] font-medium text-neutral-400 border border-neutral-500/20 capitalize">
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
            className="rounded-lg p-2 text-neutral-400 hover:bg-theme-gray-light hover:text-theme-red transition-colors shrink-0"
          >
            <LogOut className="size-4" />
          </button>
        )}
      </div>
    </div> 
  )
}
