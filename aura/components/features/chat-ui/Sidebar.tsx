"use client"

import { useEffect, useId, useRef, useState, type ReactNode } from "react"
import { useRouter } from "next/navigation"
import { AnimatePresence, motion } from "framer-motion"
import {
  MessageSquare,
  Plus,
  Trash2,
  User,
  LogOut,
  LayoutDashboard,
  Settings,
  PanelLeftClose,
  ChevronUp,
  Pencil,
} from "lucide-react"
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
  /** Desktop-only: sidebar is hidden (width collapsed to 0). */
  collapsed: boolean
  /** Desktop-only: toggle the collapsed state. */
  onCollapse: () => void
}

interface ThreadGroup {
  label: string
  threads: ChatThread[]
}

const DAY_MS = 24 * 60 * 60 * 1000

/** Buckets threads into recency groups (ChatGPT/Claude-style history), keeping input order within each. */
function groupThreadsByRecency(threads: ChatThread[]): ThreadGroup[] {
  const now = new Date()
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime()
  const startOfYesterday = startOfToday - DAY_MS
  const startOf7Days = startOfToday - 7 * DAY_MS

  const groups: ThreadGroup[] = [
    { label: "Today", threads: [] },
    { label: "Yesterday", threads: [] },
    { label: "Previous 7 days", threads: [] },
    { label: "Older", threads: [] },
  ]

  for (const thread of threads) {
    const ts = thread.updatedAt ?? 0
    if (ts >= startOfToday) groups[0].threads.push(thread)
    else if (ts >= startOfYesterday) groups[1].threads.push(thread)
    else if (ts >= startOf7Days) groups[2].threads.push(thread)
    else groups[3].threads.push(thread)
  }

  return groups.filter((g) => g.threads.length > 0)
}

export function Sidebar(props: SidebarProps) {
  return (
    <>
      <aside
        className={cn(
          "hidden shrink-0 overflow-hidden border-r border-theme-gray-light bg-theme-gray transition-[width] duration-300 ease-in-out md:block",
          props.collapsed ? "md:w-0 md:border-r-0" : "md:w-72",
        )}
        aria-hidden={props.collapsed}
      >
        <div className="h-full w-72">
          <SidebarContent {...props} />
        </div>
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
  onCollapse,
}: SidebarProps) {
  const { data: session } = useSession()
  const displayName = session?.user
    ? studentProfile.name || session.user.name || "User"
    : "Guest Account"
  const displayEmail = session?.user ? (session.user.email ?? "") : "Sign in to get started"

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between px-4 py-4">
        <div className="flex items-center gap-2.5">
          <BrandMark className="size-8 shadow-[0_0_20px_-6px_rgba(244,80,59,0.55)]" />
          <div className="flex flex-col leading-tight">
            <span className="bg-gradient-to-r from-theme-red to-theme-yellow bg-clip-text font-semibold tracking-tight text-transparent">
              AURA
            </span>
            <span className="text-[10px] text-neutral-500">Your campus AI</span>
          </div>
        </div>
        <button
          type="button"
          onClick={onCollapse}
          aria-label="Hide sidebar"
          title="Hide sidebar"
          className="hidden shrink-0 rounded-lg p-1.5 text-neutral-400 transition-colors hover:bg-theme-gray-light hover:text-neutral-100 active:scale-95 md:inline-flex"
        >
          <PanelLeftClose className="size-4" />
        </button>
      </div>

      <div className="flex flex-col gap-1 px-3">
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
        {session?.user ? (
          <a
            href="/dashboard"
            onClick={onCloseMobile}
            className="flex w-full items-center gap-2.5 rounded-xl px-3 py-2 text-sm text-neutral-400 transition-colors hover:bg-theme-gray-light/55 hover:text-neutral-100"
          >
            <LayoutDashboard className="size-4 shrink-0 text-neutral-500" />
            Dashboard
          </a>
        ) : null}
      </div>

      <nav className="chat-v2-scroll mt-4 flex-1 overflow-y-auto px-3 pb-4">
        {threads.length === 0 ? (
          <p className="px-2 py-4 text-xs text-neutral-400">No conversations yet.</p>
        ) : (
          groupThreadsByRecency(threads).map((group) => (
            <div key={group.label} className="mb-3">
              <p className="mb-1 px-2 text-[10px] font-medium uppercase tracking-wider text-neutral-600">
                {group.label}
              </p>
              <div className="space-y-1">
                {group.threads.map((thread) => {
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
                        <MessageSquare
                          className={cn("size-4 shrink-0", active && "text-theme-yellow")}
                        />
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
                })}
              </div>
            </div>
          ))
        )}
      </nav>

      <AccountFooter
        displayName={displayName}
        displayEmail={displayEmail}
        role={session?.user?.role}
        department={session?.user?.department}
        signedIn={Boolean(session?.user)}
        onOpenProfile={onOpenProfile}
        onCloseMobile={onCloseMobile}
      />
    </div>
  )
}

interface AccountFooterProps {
  displayName: string
  displayEmail: string
  role?: string
  department?: string
  signedIn: boolean
  onOpenProfile: () => void
  onCloseMobile: () => void
}

function AccountFooter({
  displayName,
  displayEmail,
  role,
  department,
  signedIn,
  onOpenProfile,
  onCloseMobile,
}: AccountFooterProps) {
  const router = useRouter()
  const [open, setOpen] = useState(false)
  const menuId = useId()
  const rootRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return

    const onPointerDown = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false)
    }

    document.addEventListener("mousedown", onPointerDown)
    document.addEventListener("keydown", onKeyDown)
    return () => {
      document.removeEventListener("mousedown", onPointerDown)
      document.removeEventListener("keydown", onKeyDown)
    }
  }, [open])

  const go = (href: string) => {
    setOpen(false)
    onCloseMobile()
    router.push(href)
  }

  return (
    <div ref={rootRef} className="relative border-t border-theme-gray-light p-3">
      <AnimatePresence>
        {open && signedIn ? (
          <motion.div
            id={menuId}
            role="menu"
            aria-label="Account menu"
            initial={{ opacity: 0, y: 6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 6, scale: 0.98 }}
            transition={{ duration: 0.14 }}
            className="absolute bottom-[calc(100%-0.25rem)] left-3 right-3 z-20 overflow-hidden rounded-xl border border-theme-gray-light bg-theme-gray shadow-2xl"
          >
            <MenuItem
              icon={<LayoutDashboard className="size-4" />}
              label="Dashboard"
              onClick={() => go("/dashboard")}
            />
            <MenuItem
              icon={<Settings className="size-4" />}
              label="Settings"
              onClick={() => go("/settings")}
            />
            <MenuItem
              icon={<Pencil className="size-4" />}
              label="Edit profile"
              onClick={() => {
                setOpen(false)
                onOpenProfile()
              }}
            />
            <div className="h-px bg-theme-gray-light" />
            <MenuItem
              icon={<LogOut className="size-4" />}
              label="Sign out"
              danger
              onClick={() => {
                setOpen(false)
                void signOut({ callbackUrl: "/login" })
              }}
            />
          </motion.div>
        ) : null}
      </AnimatePresence>

      <button
        type="button"
        aria-haspopup={signedIn ? "menu" : undefined}
        aria-expanded={signedIn ? open : undefined}
        aria-controls={signedIn && open ? menuId : undefined}
        onClick={() => {
          if (!signedIn) {
            onCloseMobile()
            router.push("/login")
            return
          }
          setOpen((prev) => !prev)
        }}
        className="flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition-colors hover:bg-theme-gray-light"
      >
        <span className="inline-flex size-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-theme-gray-lighter to-theme-gray text-neutral-200 ring-1 ring-white/10">
          <User className="size-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span
            suppressHydrationWarning
            className="flex items-center gap-1.5 truncate text-sm font-medium text-neutral-100"
          >
            <span className="truncate">{displayName}</span>
            {role ? (
              <span className="inline-flex items-center rounded-full border border-theme-yellow/20 bg-theme-yellow/10 px-1.5 py-0.5 text-[10px] font-medium capitalize text-theme-yellow">
                {role.replace("faculty_", "").replace("dean_", "dean ")}
              </span>
            ) : null}
          </span>
          {department ? (
            <span suppressHydrationWarning className="block truncate text-[10px] text-neutral-400">
              {department}
            </span>
          ) : null}
          <span suppressHydrationWarning className="block truncate text-xs text-neutral-400">
            {displayEmail}
          </span>
        </span>
        {signedIn ? (
          <ChevronUp
            className={cn(
              "size-4 shrink-0 text-neutral-500 transition-transform",
              open ? "rotate-0" : "rotate-180",
            )}
          />
        ) : null}
      </button>
    </div>
  )
}

interface MenuItemProps {
  icon: ReactNode
  label: string
  onClick: () => void
  danger?: boolean
}

function MenuItem({ icon, label, onClick, danger }: MenuItemProps) {
  return (
    <button
      type="button"
      role="menuitem"
      onClick={onClick}
      className={cn(
        "flex w-full items-center gap-2.5 px-3 py-2.5 text-left text-sm transition-colors",
        danger
          ? "text-theme-red hover:bg-theme-red/10"
          : "text-neutral-300 hover:bg-theme-gray-light hover:text-neutral-100",
      )}
    >
      <span className={cn("shrink-0", danger ? "text-theme-red" : "text-neutral-500")}>{icon}</span>
      {label}
    </button>
  )
}
